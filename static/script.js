
window.onload = async function () {

    try {

        const response = await fetch("/documents");

        const docs = await response.json();

        const select = document.getElementById("documentSelect");

        select.innerHTML = `
            <option value="">-- Select a Document --</option>
            `;
        for (const doc of docs) {

            const option = document.createElement("option");

            option.value = doc.filename;
            option.text = doc.filename;

            select.appendChild(option);

        }

    }

    catch (error) {

        console.log(error);

    }

};


const uploadForm = document.getElementById("uploadForm");

uploadForm.addEventListener("submit", async function (e) {

    e.preventDefault();

    const file = document.getElementById("documentFile").files[0];

    const message = document.getElementById("message");

    if (!file) {

        message.innerText = "Please select a document.";

        return;

    }

    const formData = new FormData();

    formData.append("file", file);

    message.innerText = "Uploading document...";

    try {

        const response = await fetch("/upload", {

            method: "POST",

            body: formData

          

        });

        const data = await response.json();

        const documentSelect = document.getElementById("documentSelect");

        const exists = [...documentSelect.options].some(
            option => option.value === data.filename
        );

        if (!exists) {

            const option = document.createElement("option");

            option.value = data.filename;
            option.text = data.filename;

            documentSelect.appendChild(option);

        }

        documentSelect.value = data.filename;

        message.innerText = data.message;

        if (data.total_pages) {

            message.innerText +=
                `

            Pages : ${data.total_pages}

            Chunks : ${data.total_chunks}`;

            }

        }

    catch (error) {

        console.log(error);

        message.innerText = "Upload Failed.";

    }

});



const askButton = document.getElementById("askBtn");

const webSearchModal = document.getElementById("webSearchModal");
const searchWebBtn = document.getElementById("searchWebBtn");
const cancelModalBtn = document.getElementById("cancelModalBtn");

async function sendQuestion(mode) {

    const question = document.getElementById("question").value;

    const filename = document.getElementById("documentSelect").value;

    const answerBox = document.getElementById("answer");

    if (question.trim() === "") {

        answerBox.innerText = "Please type a question.";

        return;

    }

    if (!filename) {

        answerBox.innerText = "Please select a document first.";

        return;

    }

    answerBox.innerText = "Thinking...";

    try {

        const response = await fetch("/ask", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                filename,   

                question,

                mode

            })

        });

        const data = await response.json();

        if (data.status === "document_not_found") {

            if (data.allow_web_search) {

                webSearchModal.classList.remove("hidden");

            } else {

                answerBox.innerText = data.message;

            }

            return;

        }

        answerBox.innerText = data.answer;

    }

    catch (error) {

        console.log(error);

        answerBox.innerText = "Something went wrong.";

    }

}

askButton.addEventListener("click", function () {

    const mode = document.getElementById("mode").value;

    sendQuestion(mode);

});

searchWebBtn.addEventListener("click", function () {

    webSearchModal.classList.add("hidden");

    sendQuestion("web");

});

cancelModalBtn.addEventListener("click", function () {

    webSearchModal.classList.add("hidden");

});