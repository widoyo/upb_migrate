var nilai = document.getElementById("nilai");
nilai.addEventListener("keyup", function(e) {
  // tambahkan 'Rp.' pada saat form di ketik
  // gunakan fungsi formatnilai() untuk mengubah angka yang di ketik menjadi format angka
  nilai.value = formatnilai(this.value, "Rp. ");
});

/* Fungsi formatnilai */
function formatnilai(angka, prefix) {
  var number_string = angka.replace(/[^,\d]/g, "").toString(),
    split = number_string.split(","),
    sisa = split[0].length % 3,
    nilai = split[0].substr(0, sisa),
    ribuan = split[0].substr(sisa).match(/\d{3}/gi);

  // tambahkan titik jika yang di input sudah menjadi angka ribuan
  if (ribuan) {
    separator = sisa ? "." : "";
    nilai += separator + ribuan.join(".");
  }

  nilai = split[1] != undefined ? nilai + "," + split[1] : nilai;
  return prefix == undefined ? nilai : nilai ? "Rp. " + nilai : "";
}