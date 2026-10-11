// ---------- 1. Find the parts of the page we need ----------
const studyForm = document.getElementById("study-form");
const studyButton = document.getElementById("study-button");
const explanationOutput = document.getElementById("explanation-output");
const keyPointsOutput = document.getElementById("key-points-output");
const flashcardsOutput = document.getElementById("flashcards-output");
const quizOutput = document.getElementById("quiz-output");
const audioStatus = document.getElementById("audio-status");
const audioPlayer = document.getElementById("audio-player");


// ---------- 2. Small helper functions ----------

// Read what the student chose in the form
function getFormValues() {
    return {
        topic: document.getElementById("topic").value.trim(),
        level: document.querySelector('input[name="level"]:checked').value,
        language: document.getElementById("language").value
    };
}

// Put every result card back to its starting message
function resetResults() {
    explanationOutput.textContent = "Your explanation will appear here.";
    keyPointsOutput.textContent = "Key points will appear here.";
    flashcardsOutput.textContent = "Flashcards will appear here.";
    quizOutput.textContent = "Your quiz will appear here.";
    audioStatus.textContent = "Audio will appear here.";
    audioPlayer.pause();
    audioPlayer.removeAttribute("src");
    audioPlayer.load();
}

// Show text in the Explanation card (keeps paragraph breaks)
function showExplanationMessage(message) {
    explanationOutput.style.whiteSpace = "pre-wrap";
    explanationOutput.textContent = message;
}

// Show the key points as a bullet list
function showKeyPoints(points) {
    keyPointsOutput.textContent = "";

    const list = document.createElement("ul");
    points.forEach(function (point) {
        const item = document.createElement("li");
        item.textContent = point;
        list.appendChild(item);
    });

    keyPointsOutput.appendChild(list);
}

// Show the flashcards: click a card to flip between question and answer
function showFlashcards(cards) {
    flashcardsOutput.textContent = "";

    const hint = document.createElement("p");
    hint.className = "flashcard-hint";
    hint.textContent = "Click a card to see the answer.";
    flashcardsOutput.appendChild(hint);

    cards.forEach(function (card) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "flashcard";

        const label = document.createElement("span");
        label.className = "flashcard-label";

        const text = document.createElement("span");
        text.className = "flashcard-text";

        let showingAnswer = false;

        // Draw the current side of the card
        function draw() {
            label.textContent = showingAnswer ? "Answer" : "Question";
            text.textContent = showingAnswer ? card.answer : card.question;
            button.classList.toggle("flipped", showingAnswer);
        }

        // Flip the card when it is clicked
        button.addEventListener("click", function () {
            showingAnswer = !showingAnswer;
            draw();
        });

        draw();
        button.appendChild(label);
        button.appendChild(text);
        flashcardsOutput.appendChild(button);
    });
}

// Show the quiz: pick an answer, see if it is right, get a score at the end
function showQuiz(questions) {
    quizOutput.textContent = "";

    let score = 0;
    let answered = 0;

    const scoreMessage = document.createElement("p");
    scoreMessage.className = "quiz-score";

    questions.forEach(function (item, number) {
        const box = document.createElement("div");
        box.className = "quiz-question";

        const title = document.createElement("p");
        title.className = "quiz-title";
        title.textContent = (number + 1) + ". " + item.question;
        box.appendChild(title);

        const optionButtons = [];

        const feedback = document.createElement("p");
        feedback.className = "quiz-feedback";

        item.options.forEach(function (optionText, optionIndex) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "quiz-option";
            button.textContent = optionText;

            button.addEventListener("click", function () {
                // Lock this question so it can only be answered once
                optionButtons.forEach(function (otherButton) {
                    otherButton.disabled = true;
                });
                answered += 1;

                if (optionIndex === item.correct_index) {
                    score += 1;
                    button.classList.add("correct");
                    feedback.textContent = "✓ " + item.explanation;
                } else {
                    button.classList.add("wrong");
                    optionButtons[item.correct_index].classList.add("correct");
                    feedback.textContent = "✗ " + item.explanation;
                }

                // After the last question, show the score
                if (answered === questions.length) {
                    scoreMessage.textContent = "Score: " + score + " / " + questions.length;
                }
            });

            optionButtons.push(button);
            box.appendChild(button);
        });

        box.appendChild(feedback);
        quizOutput.appendChild(box);
    });

    quizOutput.appendChild(scoreMessage);
}

// Turn the Study button into a "Thinking..." button (and back)
function setLoading(isLoading) {
    studyButton.disabled = isLoading;
    studyButton.textContent = isLoading ? "Thinking..." : "Study";
}

// Turn an error into a message a student can understand
function describeError(error) {
    if (error instanceof TypeError) {
        return "Could not reach the server. Is Flask still running?";
    }
    return error.message;
}


// ---------- 3. Talk to the Flask server ----------

// Send data to one of our Flask doors and wait for the answer
async function postJson(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || "Something went wrong. Please try again.");
    }

    return data;
}

// Ask for the study material: key points, flashcards and quiz
async function loadStudyMaterials(study) {
    keyPointsOutput.textContent = "Creating key points...";
    flashcardsOutput.textContent = "Creating flashcards...";
    quizOutput.textContent = "Creating your quiz...";

    try {
        const materials = await postJson("/api/materials", {
            topic: study.topic,
            explanation: study.explanation,
            language: study.language
        });
        showKeyPoints(materials.key_points);
        showFlashcards(materials.flashcards);
        showQuiz(materials.quiz);
    } catch (error) {
        keyPointsOutput.textContent = describeError(error);
        flashcardsOutput.textContent = "Flashcards could not be created this time.";
        quizOutput.textContent = "The quiz could not be created this time.";
    }
}

// Ask for the audio and put it in the player
async function loadAudio(study) {
    audioStatus.textContent = "Creating audio...";

    try {
        const result = await postJson("/api/audio", {
            text: study.explanation,
            language: study.language
        });
        audioPlayer.src = result.audio_url;
        audioPlayer.load();
        audioStatus.textContent = "Press play to listen. The text above is the transcript.";
    } catch (error) {
        audioStatus.textContent = describeError(error);
    }
}


// ---------- 4. What happens when the student clicks "Study" ----------
studyForm.addEventListener("submit", async function (event) {
    // Stop the page from reloading
    event.preventDefault();

    const values = getFormValues();

    // If the topic is empty (or only spaces), ask for a real one
    if (values.topic === "") {
        showExplanationMessage("Please type a topic first.");
        return;
    }

    // Start fresh and show a waiting message
    resetResults();
    showExplanationMessage("Thinking... this can take a few seconds.");
    setLoading(true);

    try {
        // First: the explanation (shown as soon as it arrives)
        const study = await postJson("/api/study", values);
        showExplanationMessage(study.explanation);

        // Then: the study material and the audio, both at the same time
        await Promise.all([loadStudyMaterials(study), loadAudio(study)]);
    } catch (error) {
        showExplanationMessage(describeError(error));
    } finally {
        setLoading(false);
    }
});