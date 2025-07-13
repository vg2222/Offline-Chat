const logs = document.getElementById("logs")

const message_entry = document.getElementById("message")
const loadFrame = document.getElementById("loading")

const chatLog = document.getElementById("chat-log-v2");
const template = document.querySelector('#msg-template .message-item');

const members = document.getElementById("chat-members")

let status = false
let status_response = null
let failedAttempt = 0

let current_channel = "global"
let loaded = true

let currentIP = ""

let lastMessageTime = 0;
let lastFileTime = 0;

fetch('/request-ip')
  .then(response => { return response.json(); })
  .then(data => {currentIP = data.IP;})
  .catch(error => {
    console.error('Критическая ошибка: ', error);
});

const intervalId = setInterval(() => {
    if (loaded == false) {
        loadFrame.style.display = "flex"
        return
    }
    else {
        loadFrame.style.display = "none"    
    }

    if (failedAttempt >= 2) {
        loadFrame.style.display = "flex";
    }

    status_response = fetch("http://127.0.0.1:43782/status")

    .then(response => { return response.json(); })
    .then(data => {
        failedAttempt = 0
        loadFrame.style.display = "none";

        logs.innerText = data.lastMessage
    })
    .catch(error => {
        failedAttempt = failedAttempt + 1
        console.error('Нет подключения к серверу. Ошибка:', error);
    });
}, 500); 

function send_message(isFile = false) {
    const now = Date.now();
    if (!isFile && now - lastMessageTime < 2000) {
        alert("Не удалось отправить данное сообщение, подождите 2 секунды.\n");
        return;
    }

    const message = message_entry.value.trim();
    if (!message) return;

    if (!isFile) lastMessageTime = now;

    const data = {
        "IP": currentIP,
        "Message": message,
        "To": current_channel
    };

    fetch("http://127.0.0.1:43782/send_message", {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });

    if (!isFile) message_entry.value = "";
}

document.addEventListener('keydown', (event) => {
    const keyPressed = event.key

    if (keyPressed === 'Enter') {
        send_message()
    }
});

function uploadFile() {
    const now = Date.now();
    if (now - lastFileTime < 30000) {
        alert("Не удалось отправить файл, подождите 30 секунд перед отправкой следующего.");
        return;
    }

    const fileInput = document.getElementById('file_upload');
    const file = fileInput.files[0];
    if (!file) return;

    if (file.size > 100 * 1024 * 1024) {
        alert("Не удалось отправить файл: превышен лимит в 100 МБ.");
        return;
    }

    lastFileTime = now;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("channel", current_channel);

    fetch("http://127.0.0.1:43782/upload", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.result === "ok") {
            const fileMessage = `📎 Файл: ${data.filename}`;
            const sendData = {
                "IP": currentIP,
                "Message": fileMessage,
                "To": current_channel
            };
            fetch("http://127.0.0.1:43782/send_message", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(sendData)
            });
        } else {
            alert("Не удалось отправить файл: " + data.message);
        }
    })
    .catch(err => {
        console.error("Ошибка при загрузке:", err);
    });
}


function update_members() {
    fetch("http://127.0.0.1:43782/members", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ Channel: current_channel })
    })

    .then(response_2 => response_2.json())
    .then(data => {
        if (data.members == "1") {
            members.textContent = data.members + " Участник"
            return
        }
        if (data.members == "2") {
            members.textContent = data.members + " Участника"
            return
        }
        if (data.members == "3") {
            members.textContent = data.members + " Участника"
            return
        }
        if (data.members == "4") {
            members.textContent = data.members + " Участника"
            return
        }
        if (data.members == "5") {
            members.textContent = data.members + " Участников"
        }
        else {
            members.textContent = data.members + " Участников"
        }
    })
}

  
async function load_messages() {
try {
    const res = await fetch("http://127.0.0.1:43782/get_messages", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Channel: current_channel })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const messagesArray = Object.entries(data).map(([id, meta]) => ({id, text: meta.text || meta.message || "", user: meta.user, timestamp: Number(meta.timestamp)})).sort((a, b) => a.timestamp - b.timestamp);

        chatLog.innerHTML = "";
        for (let msg of messagesArray) {
            const clone = template.cloneNode(true);
            clone.style.display = "flex";
            clone.dataset.id = msg.id;

            if (msg.user === currentIP) {
                
                clone.classList.add("message-right");
            } else {
                clone.classList.add("message-left");
            }

            clone.querySelector('.message-name').innerText = msg.user;
            clone.querySelector('.message-text').innerHTML = msg.text.startsWith("📎 Файл: ")
            ? `<a href="/uploaded/${msg.text.replace("📎 Файл: ", "").trim()}" class="file-link" target="_blank">📎 Файл: ${msg.text.replace("📎 Файл: ", "").trim()} (нажмите чтобы скачать)</a>`
            : msg.text;
            

            clone.querySelector('.message-time')
                .innerText = new Date(msg.timestamp * 1000).toLocaleString();
        chatLog.appendChild(clone);
    }
    chatLog.scrollTop = chatLog.scrollHeight;
}
catch (err) {
    console.error('Ошибка при загрузке сообщений:', err);
}
}
    
load_messages();
setInterval(load_messages, 2000);
setInterval(update_members, 2000);

  