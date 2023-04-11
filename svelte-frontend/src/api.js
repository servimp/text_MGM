import axios from "axios";

export async function fetchAvailableTags() {
  try {
    const response = await axios.get("http://localhost:8000/get_texts/");
    const allTags = response.data.flatMap((textData) => textData.tags);
    return Array.from(new Set(allTags));
  } catch (error) {
    console.error("Error fetching all texts:", error);
  }
}

export async function handleSubmit(inputText, inputTags, selectedTag) {
  try {
    const tags = [
      ...inputTags
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0), // Filter out empty strings
    ];
    if (selectedTag && selectedTag.value) {
      tags.push(selectedTag.value); // Push the value of the selected tag instead of the entire object
    }

    const response = await axios.post("http://localhost:8000/add_text/", {
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

export async function handleFilter(filterTags) {
  try {
    if (!filterTags) {
      return [];
    }
    const response = await axios.get("http://localhost:8000/get_texts_by_tags/", {
      params: { tags: filterTags },
    });
    return response.data;
  } catch (error) {
    console.error("Error filtering texts:", error);
  }
}

export async function updateTags(textId, newTags) {
  try {
    const tags = newTags.split(",").map((tag) => tag.trim());
    const response = await axios.patch(
      `http://localhost:8000/update_tags/${textId}`,
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
    const response = await axios.get("http://localhost:8000/get_texts/");
    return response.data;
  } catch (error) {
    console.error("Error fetching all texts:", error);
  }
}

export async function handleAddTags(textId, newTags) {
  try {
    const tags = newTags.split(",").map((tag) => tag.trim());
    await axios.patch(`http://localhost:8000/add_tags/${textId}`, tags);
    return tags;
  } catch (error) {
    console.error("Error adding tags:", error);
  }
}


