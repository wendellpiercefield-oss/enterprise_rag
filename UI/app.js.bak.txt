async function ask() {

    const question = document.getElementById("question").value

    document.getElementById("answer").innerText = "Thinking..."
    document.getElementById("sources").innerHTML = ""

    const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            query: question
        })
    })

    const result = await response.json()

    console.log(result)

    // Answer
    document.getElementById("answer").innerText = result.answer?.answer || "No answer returned."

    // Sources
    const sources = result.answer?.sources || []

    for (let s of sources) {

        const div = document.createElement("div")
        div.className = "source"

        const preview = (s.content || "").substring(0, 200)

        div.innerHTML = `
            <b>${s.filename || "Document"} (chunk ${s.chunk_index})</b><br>
            <span class="preview">${preview}...</span>
            <div class="full" style="display:none">${s.content}</div>
        `

        // CLICK TO EXPAND SOURCE
        div.onclick = function () {

            const full = div.querySelector(".full")

            if (full.style.display === "none") {
                full.style.display = "block"
            } else {
                full.style.display = "none"
            }

        }

        document.getElementById("sources").appendChild(div)

    }

}