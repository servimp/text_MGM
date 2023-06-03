<script>
	import { onMount } from "svelte";
	import Select from "svelte-select";
	import { 
        fetchAvailableTags,
		fetchAvailableTextTags
        } from './Api.js';
    import { 
        submit,
        onSubmitQuery,
        filterTextChanged,
        getAllTexts,
        updateTextTags,
        addTags
        } from './AppLogic.js'

    import { 
        nlpQuery,
        selectedTag,
        filterText,
        inputText,
        inputTags,
        selectedTextTag,
        filterTags,
        availableTags,
		availableTextTags,
        textList,
        nlpQueryResult
     } from "./Store.js";    

    onMount(async () => {
      const tags = await fetchAvailableTags();
    availableTags.set(tags);
	const textTags = await fetchAvailableTextTags();
    availableTextTags.set(textTags);
    });

</script>

<!-- App.svelte -->
<main class="min-h-screen bg-gray-100 flex flex-col items-center justify-center py-10">
	<div class="w-1/2 min-w-[200px] mb-4">
        <Select items={$availableTags} bind:value={$selectedTag} placeholder="Select a tag" />
	</div>

	<h1 class="text-3xl font-semibold mb-6">Text Management App</h1>

  <input
  type="text"
  bind:value="{$filterText}"
  placeholder="Enter text to filter by"
  class="w-1/2 min-w-[200px] p-2 rounded-md bg-white mb-4"
  on:input="{filterTextChanged}"
/>

	<textarea
		rows="10"
		bind:value="{$inputText}"
		placeholder="Enter your text here..."
		class="w-1/2 min-w-[200px] p-2 rounded-md bg-white resize-none mb-4"
	></textarea>
	<input
		type="text"
		bind:value="{$inputTags}"
		placeholder="Enter tags separated by commas"
		class="w-1/2 min-w-[200px] p-2 rounded-md bg-white mb-4"
	/>

	<div class="w-1/2 min-w-[200px] mb-4">
		<Select items="{$availableTextTags}" bind:value="{$selectedTextTag}" placeholder="Select a text as tag (not yet implemented)" />
	</div>
	  

	<button on:click="{submit}" class="bg-blue-600 text-white px-4 py-2 rounded-md">Submit</button>
	<h2 class="text-xl font-semibold mt-12 mb-4">Filter texts by tags</h2>
	<input
		type="text"
		bind:value="{$filterTags}"
		placeholder="Enter tags separated by commas"
		class="w-1/2 min-w-[200px] p-2 rounded-md bg-white mb-4"
	/>
	<button on:click="{filterTextChanged}" class="bg-blue-600 text-white px-4 py-2 rounded-md mb-4">Filter</button>

	<h2 class="text-xl font-semibold mt-12 mb-4">Natural Language Query</h2>
	<input
	  type="text"
	  bind:value= { $nlpQuery }
	  placeholder="Enter your natural language query"
	  class="w-1/2 min-w-[200px] p-2 rounded-md bg-white mb-4"
	/>
	<button on:click="{onSubmitQuery}" class="bg-blue-600 text-white px-4 py-2 rounded-md mb-4">Submit Query</button>
	
	<p class="mt-4">
		<strong class="font-semibold">NLP Query Result:</strong> {$nlpQueryResult}
	  </p>
	  
	<button on:click="{getAllTexts}" class="bg-blue-600 text-white px-4 py-2 rounded-md">Get All Texts</button>

	<ul class="list-none p-0 mt-8 w-full flex flex-col items-center">
		{#each $textList as textData}
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

