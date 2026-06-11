from flask import Flask, render_template, request, redirect, url_for, flash, jsonify 
from uuid import uuid4
from datetime import date, datetime

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

app.secret_key = "dev-secret-key"

tasks = []

PRIORITY_ORDER = {
    "Yüksek": 0,
    "Orta": 1,
    "Düşük": 2
}

@app.route("/")
def home():
    today_str = date.today().isoformat()

    all_tasks = list(tasks)

    # BUGÜN YAPILACAKLAR
    today_pending_tasks = sorted(
        [
            task for task in all_tasks
            if task["date"] == today_str and not task["completed"]
        ],
        key=lambda x: x.get("today_order", 0)
    )

    # BUGÜN TAMAMLANANLAR
    today_completed_tasks = sorted(
        [
            task for task in all_tasks
            if task["date"] == today_str and task["completed"]
        ],
        key=lambda x: x.get("today_order", 0)
    )

    # PROJELERE GÖRE GRUPLAMA
    project_dict = {}

    for task in all_tasks:
        project_name = task.get("project_name", "Genel")

        if project_name not in project_dict:
            project_dict[project_name] = {
                "name": project_name,
                "pending_tasks": [],
                "completed_tasks": []
            }

        if task["completed"]:
            project_dict[project_name]["completed_tasks"].append(task)
        else:
            project_dict[project_name]["pending_tasks"].append(task)

    # Proje içi sıralama: en yakın tarih üstte
    for project in project_dict.values():
        project["pending_tasks"].sort(
            key=lambda x: (x["date"], x.get("today_order", 0), x.get("order", 0))
        )
        project["completed_tasks"].sort(
            key=lambda x: (x["date"], x.get("today_order", 0), x.get("order", 0))
        )

    projects_list = sorted(
        project_dict.values(),
        key=lambda p: p["name"].lower()
    )

    return render_template(
        "index.html",
        today_pending_tasks=today_pending_tasks,
        today_completed_tasks=today_completed_tasks,
        projects=projects_list,
        today=today_str
    )

@app.route("/add", methods=["POST"])
def add_task():

    task_title = request.form.get("title", "").strip()

    project_name = request.form.get(
        "project_name",
        "Genel"
    ).strip()

    task_date = request.form.get("date", "")

    task_priority = request.form.get(
        "priority",
        "Orta"
    )

    # BOŞ KONTROLÜ
    if not task_title or not task_date:

        flash("Görev adı ve tarih boş olamaz.")

        return redirect(url_for("home"))

    # TARİH FORMAT KONTROLÜ
    try:

        selected_date = datetime.strptime(
            task_date,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        flash("Geçersiz tarih.")

        return redirect(url_for("home"))

    # GEÇMİŞ TARİH ENGELİ
    if selected_date < date.today():

        flash("Geçmiş bir tarih seçemezsin.")

        return redirect(url_for("home"))

    today_str = date.today().isoformat()

    # YENİ GÖREV
    new_task = {
        "id": str(uuid4()),
        "title": task_title,
        "date": task_date,
        "priority": task_priority,
        "completed": False,
        "order": len(tasks),
        "today_order": len([t for t in tasks if t["date"] == task_date and not t["completed"]]),
        "project_name": request.form.get("project_name", "Genel").strip()
    }

    # Eğer görev bugün içinse bugünkü listenin sonuna ekle
    if task_date == today_str:
        new_task["today_order"] = len([
            task for task in tasks
            if task["date"] == today_str and not task["completed"]
        ])

    tasks.append(new_task)

    return redirect(url_for("home"))


@app.route("/toggle/<task_id>", methods=["POST"])
def toggle_task(task_id):

    for task in tasks:

        if task["id"] == task_id:

            task["completed"] = not task["completed"]

            break

    return redirect(url_for("home"))


@app.route("/move/<task_id>/<direction>", methods=["POST"])
def move_task(task_id, direction):

    index = None

    for i, task in enumerate(tasks):

        if task["id"] == task_id:

            index = i

            break

    if index is None:

        return redirect(url_for("home"))

    # YUKARI TAŞI
    if direction == "up" and index > 0:

        tasks[index], tasks[index - 1] = (
            tasks[index - 1],
            tasks[index]
        )

    # AŞAĞI TAŞI
    elif direction == "down" and index < len(tasks) - 1:

        tasks[index], tasks[index + 1] = (
            tasks[index + 1],
            tasks[index]
        )

    return redirect(url_for("home"))


@app.route("/delete/<task_id>", methods=["POST"])
def delete_task(task_id):

    global tasks

    tasks = [
        task for task in tasks
        if task["id"] != task_id
    ]

    return redirect(url_for("home"))


@app.route("/reorder_today", methods=["POST"])
def reorder_today():
    data = request.get_json(silent=True) or {}
    ordered_ids = data.get("ordered_ids", [])

    today_str = date.today().isoformat()
    position = 0

    for task_id in ordered_ids:
        for task in tasks:
            if (
                task["id"] == task_id
                and task["date"] == today_str
                and not task["completed"]
            ):
                task["today_order"] = position
                position += 1
                break

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)

    @app.route("/reorder_today", methods=["POST"])
    def reorder_today():
        data = request.get_json()
        ordered_ids = data.get("ordered_ids", [])

        today_str = date.today().isoformat()

        today_tasks = [task for task in tasks if task["date"] == today_str and not task["completed"]]
        task_map = {task["id"]: task for task in today_tasks}

        for index, task_id in enumerate(ordered_ids):
            if task_id in task_map:
                task_map[task_id]["order"] = index

        return jsonify({"status": "ok"})