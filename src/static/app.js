document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message and dropdown
      activitiesList.innerHTML = "";
      // reset activity select options (keep the placeholder)
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;
        
        // Create participants list HTML
        const participantsList = details.participants.length > 0 
          ? `<div class="participants-section">
               <strong>Current Participants:</strong>
               <ul class="participants-list">
                 ${details.participants.map(email => `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}" title="Unregister">✕</button></li>`).join('')}
               </ul>
             </div>`
          : `<div class="participants-section">
               <strong>Current Participants:</strong>
               <p class="no-participants">No participants yet</p>
             </div>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsList}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Attach delete handlers to all delete buttons
      attachDeleteHandlers();
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "message success";
        // Refresh activities to show new participant
        await fetchActivities();
        signupForm.reset();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "message error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "message error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Function to attach delete button handlers
  async function attachDeleteHandlers() {
    const deleteButtons = document.querySelectorAll(".delete-btn");
    deleteButtons.forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.preventDefault();
        const activityName = btn.getAttribute("data-activity");
        const email = btn.getAttribute("data-email");
        
        // Confirm deletion
        if (!confirm(`Unregister ${email} from ${activityName}?`)) {
          return;
        }

        try {
          const response = await fetch(
            `/activities/${encodeURIComponent(activityName)}/unregister?email=${encodeURIComponent(email)}`,
            {
              method: "DELETE",
            }
          );

          const result = await response.json();

          if (response.ok) {
            messageDiv.textContent = result.message;
            messageDiv.className = "message success";
            // Refresh activities to reflect the removal
            fetchActivities();
          } else {
            messageDiv.textContent = result.detail || "An error occurred";
            messageDiv.className = "message error";
          }

          messageDiv.classList.remove("hidden");

          // Hide message after 5 seconds
          setTimeout(() => {
            messageDiv.classList.add("hidden");
          }, 5000);
        } catch (error) {
          messageDiv.textContent = "Failed to unregister. Please try again.";
          messageDiv.className = "message error";
          messageDiv.classList.remove("hidden");
          console.error("Error unregistering:", error);
        }
      });
    });
  }

  // Initialize app
  fetchActivities();
});
