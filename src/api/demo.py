from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/demo", response_class=HTMLResponse, include_in_schema=False)
async def demo_form() -> HTMLResponse:
    return HTMLResponse(DEMO_HTML)


DEMO_HTML = r"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MAX.Локальный Туризм — E2E demo</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Inter, system-ui, -apple-system, sans-serif;
      background: #10131a;
      color: #edf1f7;
    }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 32px 20px; }
    main { max-width: 1180px; margin: 0 auto; }
    h1 { margin: 0 0 8px; font-size: clamp(26px, 4vw, 42px); }
    .lead { margin: 0 0 28px; color: #9ea9bb; }
    .layout { display: grid; grid-template-columns: minmax(320px, 440px) 1fr; gap: 24px; }
    form, .output { background: #181d27; border: 1px solid #2a3342; border-radius: 16px; padding: 22px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    label { display: grid; gap: 7px; color: #b9c2d0; font-size: 14px; }
    label.wide { grid-column: 1 / -1; }
    input, select, textarea, button {
      width: 100%; border: 1px solid #3b4658; border-radius: 9px; padding: 11px 12px;
      background: #10141c; color: #edf1f7; font: inherit;
    }
    textarea { min-height: 78px; resize: vertical; }
    input:focus, select:focus, textarea:focus { outline: 2px solid #6e8cff; border-color: transparent; }
    .check { display: flex; align-items: center; gap: 9px; margin: 16px 0; }
    .check input { width: auto; }
    button { background: #6e8cff; border: 0; color: white; font-weight: 700; cursor: pointer; }
    button:hover { background: #829bff; }
    button:disabled { cursor: wait; opacity: .65; }
    .output { min-width: 0; }
    .output-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 14px; }
    .output h2 { margin: 0; font-size: 18px; }
    #status { color: #9ea9bb; font-size: 14px; }
    #status.error { color: #ff8e8e; }
    #status.ok { color: #78dfa5; }
    .progress-track { height: 8px; margin-bottom: 12px; overflow: hidden; border-radius: 99px; background: #0c0f15; }
    #progress-bar { width: 0; height: 100%; border-radius: inherit; background: #6e8cff; transition: width .35s ease; }
    #events { min-height: 42px; margin: 0 0 14px; padding-left: 20px; color: #9ea9bb; font-size: 12px; }
    #events li:last-child { color: #edf1f7; }
    pre {
      margin: 0; min-height: 580px; max-height: 78vh; overflow: auto; padding: 16px;
      border-radius: 10px; background: #0c0f15; color: #cbd8ec; font: 13px/1.55 ui-monospace, monospace;
      white-space: pre-wrap; overflow-wrap: anywhere;
    }
    .hint { margin-top: 12px; color: #778297; font-size: 12px; }
    @media (max-width: 850px) { .layout { grid-template-columns: 1fr; } pre { min-height: 360px; } }
    @media (max-width: 500px) { .grid { grid-template-columns: 1fr; } label.wide { grid-column: auto; } }
  </style>
</head>
<body>
<main>
  <h1>MAX.Локальный Туризм</h1>
  <p class="lead">E2E-форма backend-MVP. Результат выводится как исходный JSON.</p>
  <div class="layout">
    <form id="trip-form">
      <div class="grid">
        <label>Откуда
          <select name="origin">
            <option value="Москва" selected>Москва</option>
            <option value="Санкт-Петербург">Санкт-Петербург</option>
          </select>
        </label>
        <label>Куда <small>(пусто — выберет ИИ)</small>
          <input name="destination" placeholder="Например, Коломна">
        </label>
        <label>Дата
          <input name="start_date" type="date" required>
        </label>
        <label>Дней
          <select name="days"><option>1</option><option>2</option><option>3</option></select>
        </label>
        <label>Бюджет, ₽
          <input name="budget_rub" type="number" min="1000" value="12000" required>
        </label>
        <label>Путешественников
          <input name="travelers" type="number" min="1" max="20" value="2" required>
        </label>
        <label>Компания
          <select name="group_type">
            <option value="solo">Один</option><option value="couple" selected>Пара</option>
            <option value="friends">Друзья</option><option value="family">Семья</option>
          </select>
        </label>
        <label>Темп
          <select name="pace">
            <option value="relaxed">Спокойный</option><option value="balanced" selected>Средний</option>
            <option value="intensive">Интенсивный</option>
          </select>
        </label>
        <label>Выезд не раньше
          <input name="departure_after" type="time" value="08:00" required>
        </label>
        <label>Обратно не раньше
          <input name="return_after" type="time" value="18:00" required>
        </label>
        <label class="wide">Интересы и пожелания
          <textarea name="preferences" required>История, архитектура и местная кухня; без слишком раннего подъёма.</textarea>
        </label>
        <label class="wide">Возраст детей через запятую
          <input name="children_ages" placeholder="Например: 7, 12">
        </label>
      </div>
      <label class="check"><input name="has_car" type="checkbox"> Есть автомобиль</label>
      <button id="submit" type="submit">Сгенерировать поездку</button>
      <div class="hint">Запрос с ИИ обычно занимает 20–40 секунд.</div>
    </form>
    <section class="output">
      <div class="output-head"><h2>JSON response</h2><span id="status">Готов к запросу</span></div>
      <div class="progress-track"><div id="progress-bar"></div></div>
      <ol id="events"></ol>
      <pre id="result">{}</pre>
    </section>
  </div>
</main>
<script>
  const form = document.getElementById('trip-form');
  const result = document.getElementById('result');
  const status = document.getElementById('status');
  const submit = document.getElementById('submit');
  const progressBar = document.getElementById('progress-bar');
  const events = document.getElementById('events');
  const dateInput = form.elements.start_date;
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 2);
  dateInput.value = [tomorrow.getFullYear(), String(tomorrow.getMonth() + 1).padStart(2, '0'), String(tomorrow.getDate()).padStart(2, '0')].join('-');

  const csv = value => value.split(',').map(item => item.trim()).filter(Boolean);
  const sleep = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));

  function renderProgress(job) {
    progressBar.style.width = `${job.progress}%`;
    status.textContent = `${job.progress}% · ${job.message}`;
    events.replaceChildren(...job.events.map(item => {
      const element = document.createElement('li');
      element.textContent = `${item.progress}% — ${item.message}`;
      return element;
    }));
  }

  async function pollJob(statusUrl) {
    while (true) {
      const response = await fetch(statusUrl, {cache: 'no-store'});
      const job = await response.json();
      if (!response.ok) throw new Error(JSON.stringify(job));
      renderProgress(job);
      result.textContent = JSON.stringify(job, null, 2);
      if (job.status === 'succeeded') {
        result.textContent = JSON.stringify(job.result, null, 2);
        status.className = 'ok';
        return;
      }
      if (job.status === 'failed') {
        result.textContent = JSON.stringify(job.error, null, 2);
        status.className = 'error';
        return;
      }
      await sleep(800);
    }
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    submit.disabled = true;
    submit.textContent = 'Генерирую…';
    status.textContent = 'Запрос выполняется';
    status.className = '';
    progressBar.style.width = '0%';
    events.replaceChildren();
    result.textContent = JSON.stringify({status: 'loading'}, null, 2);

    const data = new FormData(form);
    const destination = data.get('destination').trim();
    const children = csv(data.get('children_ages')).map(Number);
    const payload = {
      origin: data.get('origin').trim(),
      start_date: data.get('start_date'),
      days: Number(data.get('days')),
      budget_rub: Number(data.get('budget_rub')),
      travelers: Number(data.get('travelers')),
      group_type: data.get('group_type'),
      children_ages: children,
      preferences: data.get('preferences').trim(),
      pace: data.get('pace'),
      has_car: data.has('has_car'),
      departure_after: data.get('departure_after'),
      return_after: data.get('return_after'),
      max_travel_minutes: 240
    };
    if (destination) payload.destination = destination;

    try {
      const response = await fetch('/api/v1/trips/jobs', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
      const body = await response.json();
      if (!response.ok) {
        result.textContent = JSON.stringify(body, null, 2);
        status.textContent = `HTTP ${response.status}`;
        status.className = 'error';
      } else {
        await pollJob(body.status_url);
      }
    } catch (error) {
      result.textContent = JSON.stringify({error: String(error)}, null, 2);
      status.textContent = 'Ошибка сети';
      status.className = 'error';
    } finally {
      submit.disabled = false;
      submit.textContent = 'Сгенерировать поездку';
    }
  });
</script>
</body>
</html>"""
