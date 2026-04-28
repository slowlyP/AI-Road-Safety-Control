document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("login-form");
  const signupForm = document.getElementById("signup-form");

  if (loginForm) {
    loginForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const loginId = document.getElementById("login_id").value.trim();
      const password = document.getElementById("password").value.trim();
      const messageBox = document.getElementById("login-message");

      try {
        const response = await fetch("/auth/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            login_id: loginId,
            password: password
          })
        });

        const result = await response.json();

        if (result.success) {
          messageBox.textContent = result.message;
          messageBox.style.color = "#4ade80";
          window.location.href = "/";
        } else {
          messageBox.textContent = result.message || "로그인에 실패했습니다.";
          messageBox.style.color = "#ff8c5a";
        }
      } catch (error) {
        messageBox.textContent = "서버 요청 중 오류가 발생했습니다.";
        messageBox.style.color = "#ff8c5a";
      }
    });
  }

  if (signupForm) {
    signupForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const username = document.getElementById("username").value.trim();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value.trim();
      const name = document.getElementById("name").value.trim();
      const messageBox = document.getElementById("signup-message");

      try {
        const response = await fetch("/auth/signup", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            username: username,
            email: email,
            password: password,
            name: name
          })
        });

        const result = await response.json();

        if (result.success) {
          messageBox.textContent = result.message;
          messageBox.style.color = "#4ade80";
          setTimeout(() => {
            window.location.href = "/auth/login";
          }, 800);
        } else {
          messageBox.textContent = result.message || "회원가입에 실패했습니다.";
          messageBox.style.color = "#ff8c5a";
        }
      } catch (error) {
        messageBox.textContent = "서버 요청 중 오류가 발생했습니다.";
        messageBox.style.color = "#ff8c5a";
      }
    });
  }
});