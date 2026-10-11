from services.gemini_service import generate_explanation, generate_study_materials

topic = "Photosynthesis"

# Step 1: get the explanation, like the website does
explanation = generate_explanation(topic, "simple", "English")

# Step 2: ask for the study material based on that explanation
materials = generate_study_materials(topic, explanation, "English")

print("KEY POINTS")
for point in materials["key_points"]:
    print("-", point)

print()
print("FLASHCARDS")
for card in materials["flashcards"]:
    print("Q:", card["question"])
    print("A:", card["answer"])
    print()

print("QUIZ")
for number, item in enumerate(materials["quiz"], start=1):
    print(f"{number}. {item['question']}")
    for index, option in enumerate(item["options"]):
        marker = "   <-- correct" if index == item["correct_index"] else ""
        print(f"   {index + 1}) {option}{marker}")
    print("   Why:", item["explanation"])
    print()