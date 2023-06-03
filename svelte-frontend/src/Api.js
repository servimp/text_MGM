import axios from "axios";

const API_URL = "http://localhost:8000";

export async function fetchAvailableTags() {
  try {
    const response = await axios.get(`${API_URL}/get_texts/`);
    const allTags = response.data.flatMap((textData) => textData.tags);
    return Array.from(new Set(allTags));
  } catch (error) {
    console.error("Error fetching all tags:", error);
  }
}

export async function fetchAvailableTextTags() {
  try {
    const response = await axios.get(`${API_URL}/get_texts/`);
    const allTags = response.data.flatMap((textData) => textData.tags);
    return Array.from(new Set(allTags));
  } catch (error) {
    console.error("Error fetching all texts as tags:", error);
  }
}

export async function handleSubmit(inputText, inputTags, selectedTag, selectedTextTag) {
  try {
    const tags = [
      ...inputTags
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0), // Filter out empty strings
    ];

    if (selectedTag && selectedTag.value) {
      tags.push(selectedTag.value);
    }

    if (selectedTextTag && selectedTextTag.value) {
      tags.push(selectedTextTag.value);
    }

    const response = await axios.post(`${API_URL}/add_text/`, {
      text: inputText,
      tags,
    });
    console.log("Text added with ID:", response.data.inserted_id);
    return {
      text: inputText,
      tags,
      _id: response.data.inserted_id,
    };
  } catch (error) {
    console.error("Error adding text:", error);
  }
}

export async function handleFilter(tags, text) {
  try {
    const response = await axios.get(
      `${API_URL}/get_texts_by_tags_and_text/?tags=${encodeURIComponent(
        tags
      )}&search=${encodeURIComponent(text)}`
    );
    return response.data || [];
  } catch (error) {
    console.error("Error filtering texts:", error);
    throw error;
  }
}



export async function updateTags(textId, newTags) {
  try {
    const tags = newTags.split(",").map((tag) => tag.trim());
    const response = await axios.patch(
      `${API_URL}/update_tags/${textId}`,
      tags,
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    console.log("Tags updated:", response.data.modified_count);
    return tags;
  } catch (error) {
    console.error("Error updating tags:", error);
  }
}

export async function handleGetAllTexts() {
  try {
    const response = await axios.get(`${API_URL}/get_texts/`);
    return response.data;
  } catch (error) {
    console.error("Error fetching all texts:", error);
  }
}

export async function handleAddTags(textId, newTags) {
  try {
    const tags = newTags.split(",").map((tag) => tag.trim());
    await axios.patch(`${API_URL}/add_tags/${textId}`, tags);
    return tags;
  } catch (error) {
    console.error("Error adding tags:", error);
  }
}

export async function handleNLPQuery(query) {
  try {
    const response = await axios.post(`${API_URL}/process_nlp_query/`, { query });
    return response.data;
  } catch (error) {
    console.error("Error handling NLP query:", error);
    throw error;
  }
}
