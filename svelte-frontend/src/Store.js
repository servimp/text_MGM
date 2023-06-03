import { writable } from 'svelte/store';
let nlpQuery = writable("");
let nlpQueryResult = writable("");
let inputText = writable("");
let inputTags = writable("");
let selectedTag = writable("");
let selectedTextTag = writable("");
let filterText = writable("");
let filterTags = writable("");
let textList = writable([]);
let availableTags = writable([]);
let availableTextTags = writable([]);


export { nlpQuery, nlpQueryResult, inputText, inputTags, selectedTag, selectedTextTag, filterTags, filterText, textList, availableTags, availableTextTags };