document.getElementById("search-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const symbol = document.getElementById("symbol").value;
    const event_type = document.getElementById("event_type").value;
    const from_date = document.getElementById("from_date").value;
    const to_date = document.getElementById("to_date").value;

    let url = `/api/v1/events?limit=50`;
    if (symbol) url += `&symbols=${symbol}`;
    if (event_type) url += `&event_type=${event_type}`;
    if (from_date) url += `&from_date=${from_date}`;
    if (to_date) url += `&to_date=${to_date}`;

    const res = await fetch(url);
    const data = await res.json();

    const tbody = document.getElementById("events-body");
    tbody.innerHTML = "";
    data.data.forEach(event => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${event.symbol}</td>
            <td>${event.event_type}</td>
            <td>${event.event_date}</td>
            <td>${event.title}</td>
            <td>${JSON.stringify(event.details)}</td>
        `;
        tbody.appendChild(tr);
    });
});
