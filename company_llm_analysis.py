import os
import csv
import openai
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up Google Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_gpt4o_response(messages):
    """
    Get a response from GPT-4o based on the conversation history
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting response from OpenAI: {e}")
        return f"Error: {str(e)}"

def get_o3_response(messages):
    """
    Get a response from OpenAI o3 model
    """
    try:
        response = openai.chat.completions.create(
            model="o3",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting response from OpenAI o3: {e}")
        return f"Error: {str(e)}"

def get_gemini_response(prompt):
    """
    Get a response from Gemini 2.0 Flash Lite
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error getting response from Gemini: {e}")
        return f"Error: {str(e)}"

def analyze_conversation(conversation_df):
    """
    Analyze the conversation using OpenAI o3 to evaluate iLoq's visibility
    """
    # Prepare the conversation data as a formatted string
    conversation_str = ""
    for _, row in conversation_df.iterrows():
        if row['Type'] == 'question':  # Only include question rows in the analysis
            conversation_str += f"Kysymys {row['QuestionNumber']} (suomeksi): {row['Question']}\n"
            conversation_str += f"Vastaus {row['QuestionNumber']} (GPT-4o): {row['GPT4o_Answer'][:500]}...\n"
            conversation_str += f"Vastaus {row['QuestionNumber']} (Gemini): {row['Gemini_Answer'][:500]}...\n\n"
            
            # Add Swedish questions and answers
            conversation_str += f"Kysymys {row['QuestionNumber']} (ruotsiksi): {row['Question_Swedish']}\n"
            conversation_str += f"Vastaus {row['QuestionNumber']} (GPT-4o): {row['GPT4o_Answer_Swedish'][:500]}...\n"
            conversation_str += f"Vastaus {row['QuestionNumber']} (Gemini): {row['Gemini_Answer_Swedish'][:500]}...\n\n"
    
    # Create the prompt for analysis
    analysis_prompt = [
        {"role": "system", "content": "You are an expert in brand analysis and marketing."},
        {"role": "user", "content": f"""Ohessa on käyttäjän kielimallille esittämät kysymykset ja kielimallin antamat vastaukset. Kysymyksiä on eri kielillä, mutta analyysi suomeksi. Arvioi miten hyvin iloq näkyy vastauksissa ja miten kielimallit esittävät iLoqin suhteessa kilpailijoihin. Lopuksi ehdota miten näkyvyyttä kielimallien osalta voisi kehittää (huomioi tekniset ja sisällölliset asiat)

{conversation_str}"""}
    ]
    
    # Get the analysis from o3
    print("Analyzing conversation with OpenAI o3...")
    analysis = get_o3_response(analysis_prompt)
    
    # Save the analysis to a text file
    analysis_file = "iloq_analysis.txt"
    with open(analysis_file, "w", encoding="utf-8") as f:
        f.write(analysis)
    
    print(f"Analysis saved to {analysis_file}")
    return analysis

def main():
    # Initialize conversation DataFrame
    conversation_df = pd.DataFrame(columns=[
        'ConversationID', 
        'QuestionNumber', 
        'Question',
        'Question_Swedish', 
        'GPT4o_Answer',
        'GPT4o_Answer_Swedish',
        'Gemini_Answer',
        'Gemini_Answer_Swedish',
        'Timestamp',
        'Type'
    ])
    
    # Generate a conversation ID (timestamp for simplicity)
    conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Define initial questions (Finnish and Swedish)
    initial_question = "Miten vaihdan älylukkoon? Kuka näitä tekee?"
    initial_question_swedish = "Hur byter jag till ett smartlås? Vilka tillverkar dessa?"
    
    # Initialize conversation history for OpenAI API (Finnish)
    gpt_messages_finnish = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": initial_question}
    ]
    
    # Initialize conversation history for OpenAI API (Swedish)
    gpt_messages_swedish = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": initial_question_swedish}
    ]
    
    # Get responses to initial questions
    print(f"Asking GPT-4o initial question in Finnish: {initial_question}")
    initial_gpt_answer = get_gpt4o_response(gpt_messages_finnish)
    
    print(f"Asking GPT-4o initial question in Swedish: {initial_question_swedish}")
    initial_gpt_answer_swedish = get_gpt4o_response(gpt_messages_swedish)
    
    print(f"Asking Gemini initial question in Finnish: {initial_question}")
    initial_gemini_answer = get_gemini_response(initial_question)
    
    print(f"Asking Gemini initial question in Swedish: {initial_question_swedish}")
    initial_gemini_answer_swedish = get_gemini_response(initial_question_swedish)
    
    # Add assistant's responses to conversation histories
    gpt_messages_finnish.append({"role": "assistant", "content": initial_gpt_answer})
    gpt_messages_swedish.append({"role": "assistant", "content": initial_gpt_answer_swedish})
    
    # Add to DataFrame
    conversation_df = pd.concat([
        conversation_df,
        pd.DataFrame([{
            'ConversationID': conversation_id,
            'QuestionNumber': 1,
            'Question': initial_question,
            'Question_Swedish': initial_question_swedish,
            'GPT4o_Answer': initial_gpt_answer,
            'GPT4o_Answer_Swedish': initial_gpt_answer_swedish,
            'Gemini_Answer': initial_gemini_answer,
            'Gemini_Answer_Swedish': initial_gemini_answer_swedish,
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Type': 'question'
        }])
    ], ignore_index=True)
    
    # Define follow-up questions
    followup_question = "Kerro lisää älylukkojen ominaisuuksista ja hinnoista?"
    followup_question_swedish = "Berätta mer om smartlåsens funktioner och priser?"
    
    # Add follow-up questions to conversation histories
    gpt_messages_finnish.append({"role": "user", "content": followup_question})
    gpt_messages_swedish.append({"role": "user", "content": followup_question_swedish})
    
    # Get responses to follow-up questions
    print(f"Asking GPT-4o follow-up question in Finnish: {followup_question}")
    followup_gpt_answer = get_gpt4o_response(gpt_messages_finnish)
    
    print(f"Asking GPT-4o follow-up question in Swedish: {followup_question_swedish}")
    followup_gpt_answer_swedish = get_gpt4o_response(gpt_messages_swedish)
    
    print(f"Asking Gemini follow-up question in Finnish: {followup_question}")
    followup_gemini_answer = get_gemini_response(followup_question)
    
    print(f"Asking Gemini follow-up question in Swedish: {followup_question_swedish}")
    followup_gemini_answer_swedish = get_gemini_response(followup_question_swedish)
    
    # Add assistant's responses to conversation histories
    gpt_messages_finnish.append({"role": "assistant", "content": followup_gpt_answer})
    gpt_messages_swedish.append({"role": "assistant", "content": followup_gpt_answer_swedish})
    
    # Add to DataFrame
    conversation_df = pd.concat([
        conversation_df,
        pd.DataFrame([{
            'ConversationID': conversation_id,
            'QuestionNumber': 2,
            'Question': followup_question,
            'Question_Swedish': followup_question_swedish,
            'GPT4o_Answer': followup_gpt_answer,
            'GPT4o_Answer_Swedish': followup_gpt_answer_swedish,
            'Gemini_Answer': followup_gemini_answer,
            'Gemini_Answer_Swedish': followup_gemini_answer_swedish,
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Type': 'question'
        }])
    ], ignore_index=True)
    
    # Define third questions
    third_question = "Vertaile eri älylukkoja ja ehdota paras"
    third_question_swedish = "Jämför olika smartlås och föreslå det bästa"
    
    # Add third questions to conversation histories
    gpt_messages_finnish.append({"role": "user", "content": third_question})
    gpt_messages_swedish.append({"role": "user", "content": third_question_swedish})
    
    # Get responses to third questions
    print(f"Asking GPT-4o third question in Finnish: {third_question}")
    third_gpt_answer = get_gpt4o_response(gpt_messages_finnish)
    
    print(f"Asking GPT-4o third question in Swedish: {third_question_swedish}")
    third_gpt_answer_swedish = get_gpt4o_response(gpt_messages_swedish)
    
    print(f"Asking Gemini third question in Finnish: {third_question}")
    third_gemini_answer = get_gemini_response(third_question)
    
    print(f"Asking Gemini third question in Swedish: {third_question_swedish}")
    third_gemini_answer_swedish = get_gemini_response(third_question_swedish)
    
    # Add assistant's responses to conversation histories
    gpt_messages_finnish.append({"role": "assistant", "content": third_gpt_answer})
    gpt_messages_swedish.append({"role": "assistant", "content": third_gpt_answer_swedish})
    
    # Add to DataFrame
    conversation_df = pd.concat([
        conversation_df,
        pd.DataFrame([{
            'ConversationID': conversation_id,
            'QuestionNumber': 3,
            'Question': third_question,
            'Question_Swedish': third_question_swedish,
            'GPT4o_Answer': third_gpt_answer,
            'GPT4o_Answer_Swedish': third_gpt_answer_swedish,
            'Gemini_Answer': third_gemini_answer,
            'Gemini_Answer_Swedish': third_gemini_answer_swedish,
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Type': 'question'
        }])
    ], ignore_index=True)
    
    # Analyze the conversation for iLoq visibility with o3
    print("\nPerforming iLoq brand visibility analysis with OpenAI o3...")
    analysis = analyze_conversation(conversation_df)
    
    # Add analysis to DataFrame
    conversation_df = pd.concat([
        conversation_df,
        pd.DataFrame([{
            'ConversationID': conversation_id,
            'QuestionNumber': 4,
            'Question': "Brändianalyysi: iLoq-brändin näkyvyys vastauksissa",
            'Question_Swedish': "Varumärkesanalys: iLoq-varumärkets synlighet i svaren",
            'GPT4o_Answer': analysis,
            'GPT4o_Answer_Swedish': "",
            'Gemini_Answer': "Analyysi tehty OpenAI o3-mallilla",
            'Gemini_Answer_Swedish': "",
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Type': 'analysis'
        }])
    ], ignore_index=True)
    
    # Save to CSV
    output_file = "company_mentions.csv"
    conversation_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Conversation and analysis saved to {output_file}")
    
    # Print summary
    print("\nConversation Summary:")
    print(f"Question 1 (Finnish): {initial_question}")
    print(f"Question 1 (Swedish): {initial_question_swedish}")
    print(f"GPT-4o Answer 1 (Finnish): {initial_gpt_answer[:100]}...")
    print(f"GPT-4o Answer 1 (Swedish): {initial_gpt_answer_swedish[:100]}...")
    print(f"Gemini Answer 1 (Finnish): {initial_gemini_answer[:100]}...")
    print(f"Gemini Answer 1 (Swedish): {initial_gemini_answer_swedish[:100]}...")
    
    print(f"Question 2 (Finnish): {followup_question}")
    print(f"Question 2 (Swedish): {followup_question_swedish}")
    print(f"GPT-4o Answer 2 (Finnish): {followup_gpt_answer[:100]}...")
    print(f"GPT-4o Answer 2 (Swedish): {followup_gpt_answer_swedish[:100]}...")
    print(f"Gemini Answer 2 (Finnish): {followup_gemini_answer[:100]}...")
    print(f"Gemini Answer 2 (Swedish): {followup_gemini_answer_swedish[:100]}...")
    
    print(f"Question 3 (Finnish): {third_question}")
    print(f"Question 3 (Swedish): {third_question_swedish}")
    print(f"GPT-4o Answer 3 (Finnish): {third_gpt_answer[:100]}...")
    print(f"GPT-4o Answer 3 (Swedish): {third_gpt_answer_swedish[:100]}...")
    print(f"Gemini Answer 3 (Finnish): {third_gemini_answer[:100]}...")
    print(f"Gemini Answer 3 (Swedish): {third_gemini_answer_swedish[:100]}...")
    
    # Print a snippet of the analysis
    print("\nAnalysis Snippet (by OpenAI o3):")
    print(analysis[:300] + "...")

if __name__ == "__main__":
    main() 