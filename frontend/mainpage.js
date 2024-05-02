// Wait for the DOM content to load
document.addEventListener("DOMContentLoaded", function() {
    // Get today's date
    var today = new Date();
    var dates = document.querySelectorAll('th[id^="date"]');
    var tempDates = [];

    // Days of the week array
    var daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    // Populate date cells with today and the next six days
    for (var i = 0; i < dates.length; i++) {
        var date = new Date(today);
        date.setDate(date.getDate() + i);
        var dayOfWeek = daysOfWeek[date.getDay()]; // Get the day of the week
        var formattedDate = date.toLocaleDateString() + " (" + dayOfWeek + ")";
        tempDates.push(formattedDate);
    }

    // Assign the dates to the table cells
    for (var i = 0; i < tempDates.length; i++) {
        dates[i].textContent = tempDates[i];
    }
});
