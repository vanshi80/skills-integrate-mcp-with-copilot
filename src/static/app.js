document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupContainer = document.getElementById("signup-container");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginMessage = document.getElementById("login-message");
  const userMenuToggle = document.getElementById("user-menu-toggle");
  const userMenu = document.getElementById("user-menu");
  const loginToggle = document.getElementById("teacher-login-toggle");
  const teacherNameDisplay = document.getElementById("teacher-name");
  const logoutButton = document.getElementById("teacher-logout");
  let teacherName = null;

  function updateAuthControls() {
    const isTeacher = Boolean(teacherName);
    signupContainer.hidden = !isTeacher;
    loginToggle.hidden = isTeacher;
    teacherNameDisplay.hidden = !isTeacher;
    teacherNameDisplay.textContent = isTeacher ? `Signed in as ${teacherName}` : "";
    logoutButton.hidden = !isTeacher;
  }

  function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `message ${type}`;
    element.classList.remove("hidden");

    setTimeout(() => {
      element.classList.add("hidden");
    }, 5000);
  }

  function handleUnauthorized(response) {
    if (response.status === 401) {
      teacherName = null;
      updateAuthControls();
      fetchActivities();
    }
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }
      const activities = await response.json();

      activitiesList.innerHTML = "";
      activitySelect.innerHTML =
        '<option value="">-- Select an activity --</option>';

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;
        const title = document.createElement("h4");
        title.textContent = name;
        const description = document.createElement("p");
        description.textContent = details.description;
        const schedule = document.createElement("p");
        schedule.innerHTML = `<strong>Schedule:</strong> ${details.schedule}`;
        const availability = document.createElement("p");
        availability.innerHTML = `<strong>Availability:</strong> ${spotsLeft} spots left`;

        activityCard.append(title, description, schedule, availability);

        const participantsContainer = document.createElement("div");
        participantsContainer.className = "participants-container";
        if (details.participants.length > 0) {
          const participantsHeading = document.createElement("h5");
          participantsHeading.textContent = "Participants:";
          const participantsList = document.createElement("ul");
          participantsList.className = "participants-list";

          details.participants.forEach((email) => {
            const participant = document.createElement("li");
            const participantEmail = document.createElement("span");
            participantEmail.className = "participant-email";
            participantEmail.textContent = email;
            participant.appendChild(participantEmail);

            if (teacherName) {
              const unregisterButton = document.createElement("button");
              unregisterButton.className = "delete-btn";
              unregisterButton.type = "button";
              unregisterButton.textContent = "Unregister";
              unregisterButton.setAttribute("aria-label", `Unregister ${email}`);
              unregisterButton.addEventListener("click", () =>
                handleUnregister(name, email)
              );
              participant.appendChild(unregisterButton);
            }

            participantsList.appendChild(participant);
          });
          participantsContainer.append(participantsHeading, participantsList);
        } else {
          const emptyMessage = document.createElement("p");
          const emptyMessageText = document.createElement("em");
          emptyMessageText.textContent = "No participants yet";
          emptyMessage.appendChild(emptyMessageText);
          participantsContainer.appendChild(emptyMessage);
        }
        activityCard.appendChild(participantsContainer);

        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  async function handleUnregister(activity, email) {
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );
      const result = await response.json();

      if (response.ok) {
        await fetchActivities();
        showMessage(messageDiv, result.message, "success");
      } else {
        handleUnauthorized(response);
        showMessage(
          messageDiv,
          result.detail || "An error occurred",
          "error"
        );
      }
    } catch (error) {
      showMessage(
        messageDiv,
        "Failed to unregister. Please try again.",
        "error"
      );
      console.error("Error unregistering:", error);
    }
  }

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );
      const result = await response.json();

      if (response.ok) {
        signupForm.reset();
        await fetchActivities();
        showMessage(messageDiv, result.message, "success");
      } else {
        handleUnauthorized(response);
        showMessage(
          messageDiv,
          result.detail || "An error occurred",
          "error"
        );
      }
    } catch (error) {
      showMessage(
        messageDiv,
        "Failed to sign up. Please try again.",
        "error"
      );
      console.error("Error signing up:", error);
    }
  });

  loginToggle.addEventListener("click", () => {
    userMenu.hidden = true;
    userMenuToggle.setAttribute("aria-expanded", "false");
    loginMessage.classList.add("hidden");
    loginDialog.showModal();
  });

  userMenuToggle.addEventListener("click", () => {
    userMenu.hidden = !userMenu.hidden;
    userMenuToggle.setAttribute("aria-expanded", String(!userMenu.hidden));
  });

  document.getElementById("cancel-login").addEventListener("click", () => {
    loginDialog.close();
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(loginForm);

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: formData.get("username"),
          password: formData.get("password"),
        }),
      });
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Unable to log in");
      }

      teacherName = result.username;
      loginForm.reset();
      loginDialog.close();
      userMenu.hidden = true;
      userMenuToggle.setAttribute("aria-expanded", "false");
      updateAuthControls();
      await fetchActivities();
    } catch (error) {
      showMessage(loginMessage, error.message, "error");
    }
  });

  logoutButton.addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to log out");
      }
      teacherName = null;
      userMenu.hidden = true;
      userMenuToggle.setAttribute("aria-expanded", "false");
      updateAuthControls();
      await fetchActivities();
    } catch (error) {
      showMessage(messageDiv, error.message, "error");
    }
  });

  async function initialize() {
    try {
      const response = await fetch("/auth/me");
      if (response.ok) {
        const result = await response.json();
        teacherName = result.username;
      }
    } catch (error) {
      console.error("Error restoring teacher session:", error);
    }

    updateAuthControls();
    await fetchActivities();
  }

  initialize();
});
