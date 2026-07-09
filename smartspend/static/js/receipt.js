
const modal = document.getElementById("imageModal");

const modalImg = document.getElementById("modalImage");

const closeBtn = document.querySelector(".close-modal");

document.querySelectorAll(".preview-image").forEach(img=>{

    img.onclick=function(){

        modal.style.display="flex";

        modalImg.src=this.src;

    };

});

closeBtn.onclick=function(){

    modal.style.display="none";

};

modal.onclick=function(e){

    if(e.target===modal){

        modal.style.display="none";

    }

};


const searchInput = document.getElementById("searchReceipt");

if (searchInput) {

    searchInput.addEventListener("keyup", function () {

        const filter = this.value.toLowerCase();

        const rows = document.querySelectorAll(".receipt-table tbody tr");

        rows.forEach(row => {

            const text = row.textContent.toLowerCase();

            if (text.includes(filter)) {

                row.style.display = "";

            } else {

                row.style.display = "none";

            }

        });

    });

}


const categoryFilter = document.getElementById("categoryFilter");

categoryFilter.addEventListener("change", function () {

    const rows = document.querySelectorAll(".receipt-table tbody tr");

    rows.forEach(function(row){

        console.log("Selected:", this.value);
        console.log("Row Category:", row.cells[4].textContent);

    }.bind(this));

});