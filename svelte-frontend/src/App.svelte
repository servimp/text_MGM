<script>
import axios from 'axios';

let inputText = '';

async function handleSubmit() {
  try {
    const response = await axios.post('http://localhost:8000/add_text/', {
      text: inputText,
    });
    console.log('Text added with ID:', response.data.inserted_id);
  } catch (error) {
    console.error('Error adding text:', error);
  }
}

  </script>
  
  <main>
	<h1>Text Management App</h1>
	<textarea
	  rows="10"
	  bind:value="{inputText}"
	  placeholder="Enter your text here..."
	></textarea>
	<button on:click="{handleSubmit}">Submit</button>
  </main>
  
  <style>
	main {
	  display: flex;
	  flex-direction: column;
	  align-items: center;
	  justify-content: center;
	  min-height: 100vh;
	}
	textarea {
	  width: 40%;
	  min-width: 200px;
	  resize: none;
	}
	button {
	  margin-top: 1rem;
	}
  </style>
  