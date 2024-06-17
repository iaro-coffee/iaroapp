function shiftTime() {
    var shiftStart = '{{shiftStart}}';
    var span = document.getElementById('clock');
    var now = new Date();
    var shiftStartDate = new Date(parseFloat(shiftStart) * 1000);
    var millis = now - shiftStartDate;
    let h, m, s;
    h = Math.floor(millis / 1000 / 60 / 60);
    m = Math.floor((millis / 1000 / 60 / 60 - h) * 60);
    s = Math.floor(((millis / 1000 / 60 / 60 - h) * 60 - m) * 60);
    s < 10 ? s = '0' + s : s = s
    m < 10 ? m = '0' + m : m = m
    h < 10 ? h = '0' + h : h = h
    span.textContent = h + ":" + m + ":" + s;
}

document.addEventListener("DOMContentLoaded", function () {

    var ongoingShift = '{{ongoingShift}}';
    var ongoingShift = (ongoingShift.toLowerCase() === "true");
    if (ongoingShift) {
        shiftTime();
        setInterval(shiftTime, 1000);
    }

    document.getElementById('ratingForm').onsubmit = function (evt) {
        evt.preventDefault();
        var ongoingShift = '{{ongoingShift}}';
        var ongoingShift = (ongoingShift.toLowerCase() === "true");
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        var errorModal = new bootstrap.Modal(document.getElementById("errorModal"), {});
        var submitModal = new bootstrap.Modal(document.getElementById("submitModal"), {});
        var alerts = document.getElementsByClassName("alert");
        for (var i = 0; i < alerts.length; i++) {
            var alert = alerts[i];
            alert.classList.add('hidden');
        }
        var form = document.querySelector('#ratingForm');
        var form_data = new FormData(form);

        let objSerializedForm = {};
        console.log(form_data);
        var star;
        for (let [name, value] of form_data) {
            if (name === "user") {
                userid = value;
            }
            if (name === "star") {
                star = value;
            }
        }
        if (star == null && ongoingShift) {
            submitModal.hide();
            errorModal.show();
            return;
        }
        objSerializedForm[userid] = { 'star': star };
        console.log(objSerializedForm);

        var request = new XMLHttpRequest();
        request.onreadystatechange = function () {
            if (request.readyState == XMLHttpRequest.DONE) {
                if (request.status == 200) {
                    var element = document.getElementsByClassName("alert-success")[0];
                    element.classList.remove("hidden");
                    location.reload(); // todo improve
                } else {
                    var element = document.getElementsByClassName("alert-danger")[0];
                    element.classList.remove("hidden");
                }
            }
            window.scrollTo(0, 0);
        }

        request.open('POST', '/shifts/');
        request.setRequestHeader("X-CSRFToken", csrftoken);
        request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        request.send(JSON.stringify(objSerializedForm));
        form.reset();
    }

    document.getElementById('punchShiftButton').onclick = function (evt) {
        var submitModal = new bootstrap.Modal(document.getElementById("submitModal"), {});
        submitModal.show();
    }

});
