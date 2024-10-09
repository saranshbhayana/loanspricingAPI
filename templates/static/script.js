document.getElementById('sendButton').onclick = function() {
    let userInput = document.getElementById('userInput').value;
    let chatlogs = document.getElementById('chatlogs');

    // Display user message
    chatlogs.innerHTML += `<p>You: ${userInput}</p>`;

    // Process the user's message
    processUserInput(userInput);

    // Clear the input field
    document.getElementById('userInput').value = '';
};

function processUserInput(input) {
    let chatlogs = document.getElementById('chatlogs');
    input = input.toLowerCase();

    if (input.includes("hi") || input.includes("hello")) {
        chatlogs.innerHTML += `<p>Chatbot: Yes, I am here to help. How can I assist you?</p>`;
    } else if (input.includes("loan")) {
        chatlogs.innerHTML += `<p>Chatbot: Yes, may I know your customer ID? I can get a personalized loan quote if you are eligible for it.</p>`;
    } else if (input.includes("customer id")) {
        // Extracting customer ID from user input if provided
        let customerId = extractCustomerId(input);
        if (customerId) {
            getLoanQuote(customerId);
        } else {
            chatlogs.innerHTML += `<p>Chatbot: Please provide your customer ID.</p>`;
        }
    } else {
        chatlogs.innerHTML += `<p>Chatbot: I'm sorry, I didn't understand that. Can you please rephrase?</p>`;
    }
}

function extractCustomerId(input) {
    // Assuming the customer ID follows the phrase "my customer ID is" 
    let regex = /my customer id is (\d+)/;
    let match = input.match(regex);
    return match ? match[1] : null; // Return customer ID if found
}

function getLoanQuote(customerId) {
    // Here you would normally make an API call to fetch the loan quote
    // For demonstration purposes, let's just simulate a response
    let chatlogs = document.getElementById('chatlogs');
    chatlogs.innerHTML += `<p>Chatbot: Fetching your loan quote for Customer ID: ${customerId}...</p>`;
    // Simulating an API call with a timeout
    setTimeout(() => {
        chatlogs.innerHTML += `<p>Chatbot: Your personalized loan quote is $5,000. Would you like to proceed?</p>`;
    }, 1000);
}
