document.addEventListener("DOMContentLoaded", () => {
    const dateInput = document.getElementById("task-date");
    const taskList = document.getElementById("today-pending-list");

    // Bugünden önce tarih seçilmesin
    if (dateInput) {
        const today = new Date().toISOString().split("T")[0];
        dateInput.min = today;
    }

    // Bugün yapılacaklar listesi yoksa çık
    if (!taskList) return;

    let draggedItem = null;

    // Sürüklenebilir görevleri bağla
    const draggableTasks = taskList.querySelectorAll(".task-card[draggable='true']");

    draggableTasks.forEach((task) => {
        task.addEventListener("dragstart", () => {
            draggedItem = task;
            task.classList.add("dragging");
        });

        task.addEventListener("dragend", () => {
            task.classList.remove("dragging");
            draggedItem = null;
            saveTaskOrder();
        });
    });

    // Sürükleme sırasında sıralama
    taskList.addEventListener("dragover", (e) => {
        e.preventDefault();

        if (!draggedItem) return;

        const afterElement = getDragAfterElement(taskList, e.clientY);

        if (afterElement == null) {
            taskList.appendChild(draggedItem);
        } else {
            taskList.insertBefore(draggedItem, afterElement);
        }
    });

    function getDragAfterElement(container, y) {
        const draggableElements = [
            ...container.querySelectorAll(".task-card:not(.dragging)")
        ];

        return draggableElements.reduce(
            (closest, child) => {
                const box = child.getBoundingClientRect();
                const offset = y - box.top - box.height / 2;

                if (offset < 0 && offset > closest.offset) {
                    return {
                        offset: offset,
                        element: child
                    };
                } else {
                    return closest;
                }
            },
            { offset: Number.NEGATIVE_INFINITY }
        ).element;
    }

    function saveTaskOrder() {
        const orderedIds = [
            ...taskList.querySelectorAll(".task-card")
        ].map((task) => task.dataset.taskId);

        fetch("/reorder_today", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                ordered_ids: orderedIds
            })
        });
    }
});