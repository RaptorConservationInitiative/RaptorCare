async function saveEvent(){

    const event = {
        type: "observation",
        ts: Date.now()
    };

    localStorage.setItem(
        Date.now(),
        JSON.stringify(event)
    );

    alert("Event saved offline");
}