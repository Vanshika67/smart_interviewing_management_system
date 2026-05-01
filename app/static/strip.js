document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.querySelector("input[type='file']");
  if (!fileInput) return;

  fileInput.addEventListener("change", () => {
    const allowed = [".pdf", ".docx", ".txt", ".md"];
    const fileName = (fileInput.value || "").toLowerCase();
    const isValid = allowed.some((ext) => fileName.endsWith(ext));
    if (!isValid) {
      alert("Please upload only PDF, DOCX, TXT, or MD file.");
      fileInput.value = "";
    }
  });
});
