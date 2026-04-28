document.addEventListener("DOMContentLoaded", function () {

  const form = document.getElementById("roleRequestForm")

  if (!form) return

  form.addEventListener("submit", async function(e){

    e.preventDefault()

    const reason = document.getElementById("request_reason").value

    const res = await fetch("/auth/role-request", {
      method:"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body: JSON.stringify({
        request_reason: reason
      })
    })

    const result = await res.json()

    const message = document.getElementById("roleMessage")

    if(result.success){
      message.innerText = "관리자 권한 신청이 완료되었습니다."
    }else{
      message.innerText = result.message
    }

  })

})