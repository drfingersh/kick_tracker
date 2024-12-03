// static/js/stopwatch.js

let timerInterval;
let elapsedTime = 0;

function startStopwatch(displayId, buttonId, inputId) {
    const display = document.getElementById(displayId);
    const button = document.getElementById(buttonId);
    const input = document.getElementById(inputId);

    if (button.innerText === 'Start') {
        button.innerText = 'Stop';
        const startTime = Date.now() - (input.value ? input.value * 1000 : 0);
        timerInterval = setInterval(() => {
            elapsedTime = Date.now() - startTime;
            const timeInSeconds = (elapsedTime / 1000).toFixed(2);
            display.innerText = timeInSeconds + ' s';
        }, 10);
    } else {
        button.innerText = 'Start';
        clearInterval(timerInterval);
        const finalTime = (elapsedTime / 1000).toFixed(2);
        input.value = finalTime;
    }
}

function resetStopwatch(displayId, buttonId, inputId) {
    clearInterval(timerInterval);
    elapsedTime = 0;
    document.getElementById(displayId).innerText = '0.00 s';
    document.getElementById(buttonId).innerText = 'Start';
    document.getElementById(inputId).value = '';
}
