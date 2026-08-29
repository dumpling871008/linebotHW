from gemini_service import ask_gemini

question = input("請輸入問題：")

answer = ask_gemini(question)

print("\nGemini 回答：")
print(answer)