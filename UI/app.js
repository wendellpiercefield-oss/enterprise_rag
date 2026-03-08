async function ask(){

const question = document.getElementById("question").value

if(!question) return

const chat = document.getElementById("chatWindow")

// show user message
chat.innerHTML += `
<div class="message user">${question}</div>
`

document.getElementById("question").value=""

// show thinking bubble
const thinking = document.createElement("div")
thinking.className="message bot"
thinking.innerText="Thinking..."
chat.appendChild(thinking)

const response = await fetch("http://localhost:8000/chat",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body: JSON.stringify({
query: question
})
})

const result = await response.json()

thinking.remove()

const answerText = result?.answer?.answer || "No answer returned."

// show assistant answer
chat.innerHTML += `
<div class="message bot">${answerText}</div>
`

chat.scrollTop = chat.scrollHeight

// render sources safely
renderSources(result?.answer?.sources || [], question)

}



function renderSources(sources, question){

const container = document.getElementById("sources")

container.innerHTML = ""

if(!sources || sources.length === 0){
    container.innerHTML = "<i>No sources returned</i>"
    return
}


// break question into keywords for highlighting
const keywords = question
    .toLowerCase()
    .replace(/[^\w\s]/g,"")
    .split(" ")
    .filter(w => w.length > 3)


for(let s of sources){

    const div = document.createElement("div")
    div.className = "source"

    const filename = s.filename || "Document"
    const chunk = s.chunk_index ?? "?"
    const sourceType = s.source || ""

    let content = s.content || ""

    // highlight keywords
    for(let k of keywords){

        const regex = new RegExp(`(${k})`,"gi")
        content = content.replace(regex,"<mark>$1</mark>")

    }

    const preview = content.substring(0,200)

    div.innerHTML = `
<b>${filename} (chunk ${chunk})</b>
<span style="color:#888">[${sourceType}]</span><br>
<span class="preview">${preview}...</span>
<div class="full">${content}</div>
`

    div.onclick = function(){

        const full = div.querySelector(".full")

        if(full.style.display === "block")
            full.style.display = "none"
        else
            full.style.display = "block"

    }

    container.appendChild(div)

}

}