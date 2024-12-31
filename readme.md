This document from Addis Ababa Science and Technology University introduces HTML and its role in web development. It explains that HTML, CSS, and JavaScript are the core web technologies, with HTML providing the structure, CSS the presentation, and JavaScript the behavior of a website.

**What is HTML?**

HTML stands for HyperText Markup Language.  "Hypertext" refers to the non-sequential linking of information (nodes), like the way web pages (HTML documents) are connected.  "Markup language" means using a set of symbols (tags) to define a document's structure, instructing the browser how to display the content, not how it looks. HTML is based on SGML (Standard Generalized Markup Language), a standard for defining markup languages.  HTML itself isn't a programming language; it simply tells the browser what to display using predefined tags.  HTML elements give meaning to pieces of text, defining their role within the document (e.g., paragraph, list item, table cell).  It structures the document into logical sections like headers, columns, and navigation menus, and allows embedding content like images and videos.

**History and Evolution:**

Before 1990, accessing and viewing documents online was difficult. Tim Berners-Lee invented the World Wide Web (WWW) in 1991, enabling centralized document storage (web servers), easy document access (web browsers), and linking between documents.  He made his invention freely available.  Before 1997, a lack of HTML standards led to browser inconsistencies.  The "War Years" (1993-1997) saw browsers implementing tags differently, creating chaos.  Around 1997, the W3C (World Wide Web Consortium) introduced HTML 4, later updated to HTML4.01, bringing standardization. The WHATWG (Web Hypertext Application Technology Working Group) was formed in 2004 by browser vendors.  HTML5, the current version, was defined in 2012 by WHATWG and is cross-platform, supported by all major browsers, and includes features like multimedia elements, graphics, offline support, and semantic markups.

**HTML Document Structure:**

A basic HTML document has a tree-like structure:

* `<!DOCTYPE html>`: Declares the HTML version.
* `<html>`: The root element containing everything.
* `<head>`: Contains meta-information (non-displayable), like the title, character set, links to stylesheets, and scripts.
* `<body>`: Contains the visible content, including text, images, multimedia, forms, etc.

**HTML Elements (Tags):**

HTML elements have a specific syntax: `<tag attribute="value">Content</tag>`.

* **Nested Elements:** Contain other HTML elements.
* **Empty Elements (Self-closing tags):**  Don't have content and use a shorthand syntax: `<tag />`.
* **Attributes:** Define properties for elements (e.g., `<img src="image.jpg" alt="Description">`).  Global attributes are common to all elements.

**Content Models:**

HTML elements are categorized based on their allowed content:

* **Block-level elements:** Start on a new line (e.g., headings, paragraphs).
* **Inline elements:** Flow within the text (e.g., bold, italic).

Modern HTML defines several content categories: metadata, flow, sectioning, heading, phrasing, embedded, and interactive.

**Key HTML Elements:**

* **Document Metadata:** `<meta>` tags provide information about the document (e.g., description, keywords, character set).
* **Text Markup:**
    * **Headings (`<h1>` to `<h6>`):** Structure the content hierarchically.
    * **Paragraphs (`<p>`):** Group related content.
    * **Preformatted Text (`<pre>`):** Preserves whitespace.
    * **Line Breaks (`<hr>`, `<br>`):** Create horizontal rules and line breaks.
    * **Lists (`<ul>`, `<ol>`, `<dl>`):** Create unordered, ordered, and description lists.
    * **Text Formatting:** `<b>`, `<i>`, `<u>`, `<strong>`, `<small>`, `<sup>`, `<sub>`, `<ins>`, `<del>`, `<mark>`, `<samp>`, `<code>`, `<kbd>`, `<var>`.
    * **Citations and Definitions:** `<cite>`, `<dfn>`.
* **HTML Entities:** Special characters represented by names (e.g., `&nbsp;`) or numbers (e.g., `&#160;`).
* **HTML Comments:** Used to add notes within the code (`<!-- comment -->`).

This summary covers the key aspects of the provided text, giving a comprehensive overview of HTML, its purpose, structure, and common elements.  It emphasizes the importance of proper HTML structure for accessibility and search engine optimization.