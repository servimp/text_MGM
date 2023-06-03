import { handleSubmit, handleFilter, updateTags, handleAddTags, handleGetAllTexts, handleNLPQuery } from './Api.js';
import { get } from 'svelte/store';
import { nlpQuery, nlpQueryResult, inputText, inputTags, selectedTag, selectedTextTag, filterTags, filterText, textList, availableTags, availableTextTags } from './Store.js';

async function getAllTexts() {
  const allTexts = await handleGetAllTexts();
  textList.set(allTexts);
}

async function onSubmitQuery() {
  try {
    console.log("nlpQuery es: ", get(nlpQuery) )
    const nlpResponse = await handleNLPQuery(get(nlpQuery));
    console.log('NLP response:', nlpResponse);
    nlpQueryResult.set(nlpResponse.response);
  } catch (error) {
    console.error('Error handling NLP query:', error);
  }
}

async function submit() {
  const newText = await handleSubmit(get(inputText), get(inputTags), get(selectedTag), get(selectedTextTag));
  textList.update((texts) => {
    texts.unshift(newText);
    return texts;
  });

  // Update availableTags with new tags, if not already in the list
  const newTags = get(inputTags)
    .split(",")
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0);
  
  if (get(selectedTag) && get(selectedTag).value) {
    newTags.push(get(selectedTag).value);
  }

  if (get(selectedTextTag) && get(selectedTextTag).value) {
    availableTextTags.update((textTags) => {
      if (!textTags.includes(get(selectedTextTag).value)) {
        return [...textTags, get(selectedTextTag).value];
      }
      return textTags;
    });
  }

  availableTags.update((tags) => {
    newTags.forEach((tag) => {
      if (!tags.includes(tag)) {
        tags.push(tag);
      }
    });
    return tags;
  });

  inputText.set("");
  inputTags.set("");  
  selectedTag.set("");
  selectedTextTag.set("");
}


async function addTags(textId, newTags) {
  const addedTags = await handleAddTags(textId, newTags);
  textList.update((texts) => {
    return texts.map((text) => {
      if (text._id === textId) {
        text.tags.push(...addedTags);
      }
      return text;
    });
  });
}

async function updateTextTags(textId, newTags) {
  const updatedTags = await updateTags(textId, newTags);
  textList.update((texts) => {
    const textToUpdateIndex = texts.findIndex((text) => text._id === textId);
    if (textToUpdateIndex !== -1) {
      texts[textToUpdateIndex].tags = updatedTags;
      return [...texts];
    }
    return texts;
  });
}

async function filterTextChanged() {
  const filterTagsValue = get(filterTags).trim(); // Convert array to a comma-separated string and then trim
  const filterTextValue = get(filterText).trim(); // Trim the string

  if (filterTagsValue.length > 0 || filterTextValue.length > 0) {
    const filteredTextList = await handleFilter(filterTagsValue, filterTextValue);
    textList.set(filteredTextList);
  } else {
    const allTexts = await handleGetAllTexts();
    textList.set(allTexts);
  }
}

export {
  onSubmitQuery, submit, getAllTexts, addTags, updateTextTags, filterTextChanged
};