// websocket
const baseUrl = "https://teaching-lark-included.ngrok-free.app/requests";
const username = localStorage.getItem("username") || "guest";
const wsUrl = `wss://teaching-lark-included.ngrok-free.app/ws/${username}`;
let socket;

function connectWebSocket() {
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("WebSocket connection established");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("WebSocket message received:", data);

    if (data.type === "heartbeat") {
      console.log("Heartbeat received:", data.timestamp);
    } else if (data.events && Array.isArray(data.events)) {
      updateTable(data.events);
    }

    const updatedAt = document.getElementById("updated-at");
    updatedAt.textContent = `Last updated: ${new Date().toLocaleString()}`;
  };

  socket.onclose = () => {
    console.error("WebSocket connection closed. Reconnecting...");
    setTimeout(connectWebSocket, 5000);
  };

  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
  };
}

function updateTable(events) {
  const tableBody = document.querySelector("#webhook-table tbody");
  tableBody.innerHTML = "";

  events.forEach((event) => {
    const student = event.data;
    const row = document.createElement("tr");
    row.innerHTML = `
          <td>${student.id}</td>
          <td>${student.name}</td>
          <td>${student.school_id}</td>
          <td>${student.age}</td>
          <td>${student.total_score}</td>
          <td>${student.mobile}</td>
        `;
    tableBody.appendChild(row);
  });
}
connectWebSocket();

// student manaagent
function debounceLoadStudents() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(loadStudents, debounceDelay);
}

function showSuccessMessage(message) {
  const alertBox = document.createElement("div");
  alertBox.className = "alert alert-success alert-dismissible fade show";
  alertBox.role = "alert";
  alertBox.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      `;
  document.body.appendChild(alertBox);

  setTimeout(() => {
    alertBox.remove();
  }, 3000);
}
function SearchActiveStudent() {
  var username = localStorage.getItem("username");
  if (username) {
    fetch("https://teaching-lark-included.ngrok-free.app/search-odoo", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username }),
    })
      .then((response) => {
        if (response.status === 401) {
          alert("Unauthorized: Please login into Odoo first.");
          throw new Error("Unauthorized");
        }
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        const tableBody = document.querySelector(
          "#active-students-table tbody"
        );

        tableBody.innerHTML = "";

        if (!data.students || data.students.length === 0) {
          const noDataRow = document.createElement("tr");
          noDataRow.innerHTML = `
            <td colspan="6" style="text-align: center;">No active students found</td>
          `;
          tableBody.appendChild(noDataRow);
          return;
        }

        data.students.forEach((student) => {
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${student.id}</td>
            <td>${student.name}</td>
            <td>${student.school_id ? student.school_id[1] : "N/A"}</td>
            <td>${student.age || "N/A"}</td>
            <td>${student.total_score || "N/A"}</td>
            <td>${student.mobile || "N/A"}</td>
          `;
          tableBody.appendChild(row);
        });
      })
      .catch((error) => {
        console.error("Error during API call:", error);
        alert("Failed to fetch active students. Please try again.");
      });
  } else {
    alert("Please login into Odoo first.");
  }
}

function saveChanges() {
  var username = document.getElementById("userName").value.trim();
  var db_name = document.getElementById("db_name").value.trim();
  var password = document.getElementById("password").value.trim();

  var modal = bootstrap.Modal.getInstance(
    document.getElementById("exampleModal")
  );

  if (!username || !db_name || !password) {
    showErrorMessage("All fields are required!");
    return;
  }

  const data = {
    username: username,
    db_name: db_name,
    password: password,
  };

  fetch("http://127.0.0.1:8000/odoo-login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Login successful:", data);
      showSuccessMessage("Login successful!");

      localStorage.setItem("username", username);

      modal.hide();
    })
    .catch((error) => {
      console.error("Error during API call:", error);
      showErrorMessage(
        "Login failed. Please check your credentials and try again."
      );
    });
}

async function CreateNewOdooStudent() {
  function formatDate(date) {
    const parts = date.split("/");
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  }

  const studentName = document.getElementById("student_name").value.trim();
  const dob = document.getElementById("dob").value.trim();
  const mobile = document.getElementById("mobile").value.trim();
  const totalScore = document.getElementById("total_score").value.trim();

  const modal = bootstrap.Modal.getInstance(
    document.getElementById("createNewStudentModal")
  );

  if (!studentName || !dob || !mobile || !totalScore) {
    showErrorMessage("All fields are required!");
    return;
  }

  const formattedDob = formatDate(dob);
  const tableBody = document.querySelector("#create-students-table tbody");

  tableBody.innerHTML = "";

  const data = {
    username: localStorage.getItem("username"),
    student_name: studentName,
    dob: formattedDob,
    mobile: mobile,
    total_score: totalScore,
  };

  try {
    const response = await fetch("http://localhost:8000/create-odoo", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const responseData = await response.json();

    showSuccessMessage(
      `Student data created successfully! Record ID: ${responseData.id} is created`
    );

    modal.hide();

    res = await fetch("http://localhost:8000/search-created-student-odoo", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: localStorage.getItem("username"),
        student_id: responseData.id,
      }),
    });

    if (!res.ok) {
      throw new Error(`API error: ${res.status}`);
    }

    const resData = await res.json();
    resData.students.forEach((student) => {
      const row = document.createElement("tr");
      row.innerHTML = `
            <td>${student.id}</td>
            <td>${student.name}</td>
            <td>${student.school_id ? student.school_id[1] : "N/A"}</td>
            <td>${student.age || "N/A"}</td>
            <td>${student.total_score || "N/A"}</td>
            <td>${student.mobile || "N/A"}</td>
          `;
      tableBody.appendChild(row);
    });
  } catch (error) {
    console.error("Error during API call:", error);
    showErrorMessage("Failed to save student data. Please try again later.");
  }
}

function showSuccessMessage(message) {
  alert(message);
}

function showErrorMessage(message) {
  alert(message);
}

function showSuccessMessage(message) {
  const alertBox = document.createElement("div");
  alertBox.className = "alert alert-success alert-dismissible fade show";
  alertBox.role = "alert";
  alertBox.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      `;
  document.body.appendChild(alertBox);

  setTimeout(() => {
    alertBox.remove();
  }, 3000);
}

function showErrorMessage(message) {
  const alertBox = document.createElement("div");
  alertBox.className = "alert alert-danger alert-dismissible fade show";
  alertBox.role = "alert";
  alertBox.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      `;
  document.body.appendChild(alertBox);

  setTimeout(() => {
    alertBox.remove();
  }, 3000);
}

window.onload = () => {
  connectWebSocket();

  setInterval(() => {
    if (socket.readyState !== WebSocket.OPEN) {
      console.log("WebSocket is not open. Attempting to reconnect...");
      connectWebSocket();
    }
  }, 10000);
};

window.onbeforeunload = () => {
  if (socket) {
    socket.close();
  }
};

$(document).ready(function () {
  $("#dob").datepicker({
    format: "mm/dd/yyyy",
    autoclose: true,
    todayHighlight: true,
  });
});
