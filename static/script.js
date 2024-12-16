function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const mainContent = document.getElementById("main-content");
  
    if (sidebar.style.left === "-250px") {
        sidebar.style.left = "0";
        mainContent.style.marginLeft = "250px";
    } else {
        sidebar.style.left = "-250px";
        mainContent.style.marginLeft = "0";
    }
  }
  
  document.addEventListener("DOMContentLoaded", function() {
    const accordions = document.querySelectorAll(".accordion");
  
    accordions.forEach((accordion) => {
        const header = accordion.querySelector(".accordion-header");
  
        header.addEventListener("click", () => {
            accordion.classList.toggle("open");
            const content = accordion.querySelector(".accordion-content");
  
            if (accordion.classList.contains("open")) {
                content.style.display = "block";
            } else {
                content.style.display = "none";
            }
        });
    });
  });
  
  // Fungsi untuk mengunduh file Excel
  function downloadExcel() {
    window.location.href = "/download-excel";
  }
  
  function getCurrentTime() {
    var now = new Date();
    var hours = now.getHours().toString().padStart(2, '0');
    var minutes = now.getMinutes().toString().padStart(2, '0');
    return hours + ':' + minutes;
  }
  
  function addComment() {
    var nameInput = document.getElementById('name-input');
    var commentInput = document.getElementById('comment-input');
    var anonymousCheckbox = document.getElementById('anonymous-checkbox');
    var commentText = commentInput.value.trim();
    var name = nameInput.value.trim();
    var time = getCurrentTime();  // Dapatkan waktu saat ini
  
    if (commentText === "") {
        alert("Please enter a comment.");
        return;
    }
  
    if (anonymousCheckbox.checked) {
        name = "Anonymous";
        nameInput.disabled = true;
    } else if (name === "") {
        alert("Please enter your name or check 'Post as Anonymous'.");
        return;
    }
  
    var commentsList = document.getElementById('comments-list');
    var newComment = document.createElement('div');
    newComment.className = 'comment';
    newComment.innerHTML = `<strong>${name}</strong>: ${commentText} <span class="comment-time">${time}</span><br><button class="reply-button" style="margin-top: 10px;" onclick="showReplyForm(this)">Reply</button>`;
    commentsList.appendChild(newComment);
  
    commentInput.value = "";
    nameInput.value = "";
    anonymousCheckbox.checked = false;
    nameInput.disabled = false;
  }
  
  document.getElementById('anonymous-checkbox').addEventListener('change', function() {
    var nameInput = document.getElementById('name-input');
    if (this.checked) {
        nameInput.disabled = true;
    } else {
        nameInput.disabled = false;
    }
  });
  
  function showReplyForm(button) {
    var replyForm = document.createElement('div');
    replyForm.className = 'reply-form';
    replyForm.innerHTML = `
        <label for="reply-name">Name:</label>
        <input type="text" id="reply-name" class="reply-name" placeholder="Your Name">
        <div class="checkbox-container">
            <input type="checkbox" id="reply-anonymous" class="reply-anonymous">
            <label for="reply-anonymous" class="anonymous-checkbox-label">Post as Anonymous</label>
        </div>
        <label for="reply-input">Add a Reply:</label>
        <textarea id="reply-input" class="reply-input" rows="2" placeholder="Your reply"></textarea>
        <button type="button" class="reply-button" onclick="addReply(this)">Submit</button>
    `;
    button.parentElement.appendChild(replyForm);
    button.style.display = 'none';
    replyForm.style.display = 'block';
  
    document.getElementById('reply-anonymous').addEventListener('change', function() {
        var replyNameInput = document.getElementById('reply-name');
        if (this.checked) {
            replyNameInput.disabled = true;
        } else {
            replyNameInput.disabled = false;
        }
    });
  }
  
  function addReply(button) {
    var replyForm = button.parentElement;
    var replyNameInput = replyForm.querySelector('.reply-name');
    var replyInput = replyForm.querySelector('.reply-input');
    var replyAnonymousCheckbox = replyForm.querySelector('.reply-anonymous');
    var replyText = replyInput.value.trim();
    var replyName = replyNameInput.value.trim();
    var time = getCurrentTime();  // Dapatkan waktu saat ini
  
    if (replyText === "") {
        alert("Please enter a reply.");
        return;
    }
  
    if (replyAnonymousCheckbox.checked) {
        replyName = "Anonymous";
    } else if (replyName === "") {
        alert("Please enter your name or check 'Post as Anonymous'.");
        return;
    }
  
    var reply = document.createElement('div');
    reply.className = 'reply';
    reply.innerHTML = `<strong>${replyName}</strong>: ${replyText} <span class="comment-time">${time}</span>`;
    replyForm.parentElement.appendChild(reply);
    replyForm.remove();
  }