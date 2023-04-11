<script>
	import { onMount } from "svelte";
	import Select from "svelte-select";
	import { handleSubmit, handleFilter, updateTags, handleAddTags, fetchAvailableTags, handleGetAllTexts } from './api.js';



	let inputText = "";
	let inputTags = "";
	let filterTags = "";
	let textList = [];
	let availableTags = [];
	let nlpQuery = "";


	let selectedTag = { value: "" };

	onMount(async () => {
	availableTags = await fetchAvailableTags();
	});

	async function handleNLPQuery() {
  // This function will be implemented later
}

	// Wrapper functions for API calls
	async function submit() {
		const newText = await handleSubmit(inputText, inputTags, selectedTag);
		textList.unshift(newText);
		inputText = "";
		inputTags = "";
		selectedTag = "";
	}

	async function filter() {
		const filteredTextList = await handleFilter(filterTags);
		textList = filteredTextList;
	}

	async function getAllTexts() {
		const allTexts = await handleGetAllTexts();
		textList = allTexts;
	}

	async function addTags(textId, newTags) {
		const addedTags = await handleAddTags(textId, newTags);
		textList = textList.map((text) => {
			if (text._id === textId) {
				text.tags.push(...addedTags);
			}
			return text;
		});
	}

	async function updateTextTags(textId, newTags) {
		const updatedTags = await updateTags(textId, newTags);
		const textToUpdateIndex = textList.findIndex((text) => text._id === textId);
		if (textToUpdateIndex !== -1) {
			textList[textToUpdateIndex].tags = updatedTags;
			textList = textList.slice(); // Trigger reactivity by creating a new reference
		}
	}
</script>

<!-- App.svelte -->
<main class="min-h-screen bg-gray-100 flex flex-col items-center justify-center py-10">
	<div class="w-1/2 min-w-[200px] mb-4">
		<Select items="{availableTags}" bind:value="{selectedTag}" placeholder="Select a tag" />
	</div>

	<h1 class="text-3xl font-semibold mb-6">Text Management App</h1>
	<textarea
		rows="10"
		bind:value="{inputText}"
		placeholder="Enter your text here..."
		class="w-1/2 min-w-[200px] p-2 rounded-md bg-white resize-none mb-4"
	></textarea>
	<input
		type="text"
		bind:value="{inputTags}"
		placeholder="Enter tags separated by commas"
		class="w-1/2 min-w-[200px] p-2 rounded-md bg-white mb-4"
	/>
	<button on:click="{submit}" class="bg-blue-600 text-white px-4 py-2 rounded-md">Submit</button>
	<h2 class="text-xl font-semibold mt-12 mb-4">Filter texts by tags</h2>
	<input
		type="text"
		bind:value="{filterTags}"
		placeholder="Enter tags separated by commas"
		class="w-1/2 min-w-[200px] p-2 rounded-md bg-white mb-4"
	/>
	<button on:click="{filter}" class="bg-blue-600 text-white px-4 py-2 rounded-md mb-4">Filter</button>


	<h2 class="text-xl font-semibold mt-12 mb-4">Natural Language Query</h2>
	<input
	  type="text"
	  bind:value="{nlpQuery}"
	  placeholder="Enter your natural language query"
	  class="w-1/2 min-w-[200px] p-2 rounded-md bg-white mb-4"
	/>
	<button on:click="{handleNLPQuery}" class="bg-blue-600 text-white px-4 py-2 rounded-md mb-4">Submit Query</button>
	


	<button on:click="{getAllTexts}" class="bg-blue-600 text-white px-4 py-2 rounded-md">Get All Texts</button>

	<ul class="list-none p-0 mt-8 w-full flex flex-col items-center">
		{#each textList as textData}
		<li class="bg-white p-6 rounded-md shadow-lg w-1/2 min-w-[200px] mb-8">
			<div class="mb-4">
				<strong class="font-semibold">Text:</strong> {textData.text}
			</div>
			<div class="mb-4">
				<strong class="font-semibold">Tags:</strong> {textData.tags ? textData.tags.join(", ") : ""}
			</div>
			<div class="mb-4">
				<input
					type="text"
					bind:value="{textData.newTags}"
					placeholder="Update tags separated by commas"
					class="w-full p-2 rounded-md bg-gray-100"
				/>
				<button on:click={() => updateTextTags(textData._id, textData.newTags)} class="bg-green-600 text-white px-4 py-2 rounded-md mt-2">Update Tags</button>
			</div>
			<div>
				<input
					type="text"
					bind:value="{textData.newTagsToAdd}"
					placeholder="Add tags separated by commas"
					class="w-full p-2 rounded-md bg-gray-100"
				/>
				<button on:click={() => addTags(textData._id, textData.newTagsToAdd)} class="bg-yellow-600 text-white px-4 py-2 rounded-md mt-2">Add Tags</button>
			</div>
		</li>
		{/each}
	</ul>
</main>

<!-- Add this line to import the Tailwind CSS styles -->
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.17/dist/tailwind.min.css" rel="stylesheet">

