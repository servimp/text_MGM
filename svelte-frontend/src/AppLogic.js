import { onMount } from "svelte";
import { handleSubmit, handleFilter, updateTags, handleAddTags, fetchAvailableTags, handleGetAllTexts, handleNLPQuery } from './api.js';

let inputText = "";
let inputTags = "";
let filterTags = "";
let textList = [];
let availableTags = [];
let nlpQuery = "";
let nlpQueryResult = "";

let selectedTextTag = { value: "" };

let filterText = "";

let selectedTag = { value: "" };

onMount(async () => {
	availableTags = await fetchAvailableTags();
	});

	async function onSubmitQuery() {
  try {
    const nlpResponse = await handleNLPQuery(nlpQuery);
    console.log('NLP response:', nlpResponse);
    nlpQueryResult = nlpResponse.response;
  } catch (error) {
    console.error('Error handling NLP query:', error);
  }
}

	// Wrapper functions for API calls
	async function submit() {
  const newText = await handleSubmit(inputText, inputTags, selectedTag, selectedTextTag);
  textList.unshift(newText);
  inputText = "";
  inputTags = "";
  selectedTag = "";
  selectedTextTag = "";
}


async function filter() {
  if (filterTags.trim().length > 0 || filterText.trim().length > 0) {
    const filteredTextList = await handleFilter(filterTags, filterText);
    textList = filteredTextList;
  } else {
    textList = await handleGetAllTexts();
  }
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


	async function filterTextChanged() {
  if (filterTags.trim().length > 0 || filterText.trim().length > 0) {
    textList = await handleFilter(filterTags, filterText);
  } else {
    textList = await handleGetAllTexts();
  }
}


export {
  inputText, inputTags, filterTags, textList, availableTags, nlpQuery, nlpQueryResult,
  selectedTextTag, filterText, selectedTag,
  onSubmitQuery, submit, filter, getAllTexts, addTags, updateTextTags, filterTextChanged
};