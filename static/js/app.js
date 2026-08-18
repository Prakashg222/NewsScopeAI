document.addEventListener("DOMContentLoaded", function () {

    // ============================================================
    // FILE UPLOAD - SHOW SELECTED FILE
    // ============================================================

    const fileInput = document.getElementById("file");
    const selectedFile = document.getElementById("selectedFile");

    if (fileInput && selectedFile) {

        fileInput.addEventListener("change", function () {

            if (this.files.length > 0) {

                selectedFile.classList.remove("d-none");

                const fileNameSpan =
                    selectedFile.querySelector("span");

                if (fileNameSpan) {
                    fileNameSpan.textContent =
                        this.files[0].name;
                }

            } else {

                selectedFile.classList.add("d-none");

            }

        });

    }


    // ============================================================
    // NOTIFICATION ALERT - AUTO CLOSE
    // ============================================================

    document
        .querySelectorAll(".notification-alert")
        .forEach(function (alert) {

            setTimeout(function () {

                if (
                    typeof bootstrap !== "undefined" &&
                    bootstrap.Alert
                ) {

                    const instance =
                        bootstrap.Alert.getOrCreateInstance(
                            alert
                        );

                    instance.close();

                } else {

                    alert.remove();

                }

            }, 5000);

        });


    // ============================================================
    // NAVBAR SCROLL EFFECT
    // ============================================================

    function updateNavbar() {

        const navbar =
            document.querySelector(".glass-nav");

        if (navbar) {

            navbar.classList.toggle(
                "nav-scrolled",
                window.scrollY > 20
            );

        }

    }


    window.addEventListener(
        "scroll",
        updateNavbar
    );


    // Run once when page loads

    updateNavbar();


    // ============================================================
    // CATEGORY PROGRESS BARS
    // ============================================================

    document
        .querySelectorAll(".category-progress")
        .forEach(function (bar) {

            const count =
                Number(bar.dataset.count || 0);

            const total =
                Number(bar.dataset.total || 0);

            let percentage = 0;

            if (total > 0) {

                percentage =
                    (count / total) * 100;

            }

            // Keep between 0 and 100

            percentage =
                Math.max(
                    0,
                    Math.min(
                        percentage,
                        100
                    )
                );

            bar.style.width =
                percentage + "%";

            bar.setAttribute(
                "aria-valuenow",
                count
            );

        });


    // ============================================================
    // CONFIDENCE PROGRESS BARS
    // ============================================================

    document
        .querySelectorAll(".confidence-bar")
        .forEach(function (bar) {

            const confidence =
                Number(
                    bar.dataset.confidence || 0
                );

            const percentage =
                Math.max(
                    0,
                    Math.min(
                        confidence,
                        100
                    )
                );

            bar.style.width =
                percentage + "%";

        });


    // ============================================================
    // SENTIMENT SCORE PROGRESS BARS
    // ============================================================

    document
        .querySelectorAll(".score-bar")
        .forEach(function (bar) {

            const score =
                Number(
                    bar.dataset.score || 0
                );

            const percentage =
                Math.max(
                    0,
                    Math.min(
                        score,
                        100
                    )
                );

            bar.style.width =
                percentage + "%";

        });

});


// ============================================================
// DELETE CONFIRMATION
// ============================================================
let deleteForm = null;

function confirmDelete(form) {
    deleteForm = form;
    document.getElementById("deleteModal").classList.add("show");
    return false;
}

function closeDeleteModal() {
    document.getElementById("deleteModal").classList.remove("show");
    deleteForm = null;
}

function deleteArticle() {
    if (deleteForm) {
        deleteForm.submit();
    }
}