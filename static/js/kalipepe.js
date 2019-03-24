/**
 * @fileoverview Menggambar Tinggi Muka Air dari 3 POS yang diberikan
 * input var Poses = []
 * @package
 */
//Inisialisasi variabel
let draw = SVG("drawing");
let viewboxWidth = Object.values(draw.viewbox())[2];
let viewboxHeight = Object.values(draw.viewbox())[3];

let padding = 24;
//if else untuk padding
if (window.innerWidth <= 640) {
  padding = 12;
} 

let yRevert = function (yBeforeRevert) {
  //return viewboxHeight - yBeforeRevert; //menukar posisi y0 dengan y maksimum kanvas
  return (viewboxHeight * 90 / 100) - yBeforeRevert; //menukar posisi y0 dengan 90% kanvas
}

let yScaling = function (yInput) {
  //return ((yInput - hMin) / (hMaks - hMin)) * viewboxHeight; //y = maksimum kanvas 
  return ((yInput - hMin) / (hMaks - hMin)) * (viewboxHeight * 80 / 100) //y = 80% kanvas;
}

class posTMA {
  constructor(opt) {
    this.pId = opt.id;
    this.namaPos = opt.nama;
    this.dasar = opt.dasar;
    this.sh = opt.dasar + opt.sh;
    this.sk = opt.dasar + opt.sk;
    this.sm = opt.dasar + opt.sm;
		this.ll = opt.ll;
  }
  startDraw(ox = 0, oy = 0) {
    this.ox = ox;
    this.oy = oy;
    draw.line(this.ox, this.oy + yRevert(yScaling(hMin)),
      this.ox, this.oy + yRevert(yScaling(this.sm + 0.5)))
      .stroke({ color: '#666', width: 10 });//IndikatorBar
    draw.line(this.ox - (10 / 2), this.oy + yRevert(yScaling(this.dasar)),
      this.ox + (10 / 2), this.oy + yRevert(yScaling(this.dasar)))
      .stroke({ color: '#000', width: 1.7 });//Garis Dasar
    draw.text(this.dasar.toString())
      .x(this.ox + 30).cy(this.oy + yRevert(yScaling(this.dasar)))
      .font({ size: 12, anchor: 'start' })
      .fill({ color: '#000' });//draw teks garis dasar
    draw.polygon().plot([[this.ox + 5, this.oy + yRevert(yScaling(this.sh))],
    [this.ox + 25, this.oy + yRevert(yScaling(this.sh))],
    [this.ox + 25, this.oy + yRevert(yScaling(this.sk))],
    [this.ox + 5, this.oy + yRevert(yScaling(this.sk))]])
      .fill({ color: '#3f3' });//BarSiagaHijau
    draw.text(this.sh.toString())
      .x(this.ox + 30).cy(this.oy + yRevert(yScaling(this.sh)))
      .font({ size: 12, anchor: 'start' })
      .fill({ color: '#0f0' })
      .stroke({ color: '#000', width: '0.5' });//draw sh text
    draw.polygon().plot([[this.ox + 5, this.oy + yRevert(yScaling(this.sk))],
    [this.ox + 25, this.oy + yRevert(yScaling(this.sk))],
    [this.ox + 25, this.oy + yRevert(yScaling(this.sm))],
    [this.ox + 5, this.oy + yRevert(yScaling(this.sm))]])
      .fill('#ff3');//BarSiagaKuning
    draw.text(this.sk.toString())
      .x(this.ox + 30).cy(this.oy + yRevert(yScaling(this.sk)))
      .font({ size: 12, anchor: 'start' }).fill({ color: '#ff0' })
      .stroke({ color: '#000', width: '0.5' });//draw sk text
    draw.polygon().plot([[this.ox + 5, this.oy + yRevert(yScaling(this.sm))],
    [this.ox + 25, this.oy + yRevert(yScaling(this.sm))],
    [this.ox + 25, this.oy + yRevert(yScaling(this.sm + 0.5))],
    [this.ox + 5, this.oy + yRevert(yScaling(this.sm + 0.5))]])
      .fill('#f33');//BarSiagaMerah
    draw.text(this.sm.toString())
      .x(this.ox + 30).cy(this.oy + yRevert(yScaling(this.sm)))
      .font({ size: 12, anchor: 'start' })
      .fill({ color: '#f00' })
      .stroke({ color: '#000', width: '0.5' });//draw sm text
    draw.text(this.namaPos.toString()).x(this.ox).cy(this.oy + yRevert(0) + 15)
      .font({ size: 14, anchor: 'middle' })
      .fill({ color: '#000' })
      .stroke({ color: '#111', width: '0.5' });//draw Pos text
  }

	distanceTo(obj) {
		const lat1 = this.ll.split(', ')[0];
		const lon1 = this.ll.split(', ')[1];
		const lat2 = obj.ll.split(', ')[0];
		const lon2 = obj.ll.split(', ')[1];
		const R = 6371; // km (change this constant to get miles)
		const dLat = (lat2 - lat1) * Math.PI / 180;
		const  dLon = (lon2 - lon1) * Math.PI / 180;
		const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
			Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
			Math.sin(dLon / 2) * Math.sin(dLon / 2);
		return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
	}

  updateTMA(tma) {
    draw.circle(20).cx(this.ox).cy(this.oy + yRevert(yScaling(tma)))
      .fill('#ff0')
      .stroke({ color: '#000', width: 1 });//draw tma circle
    draw.text(tma.toString()).x(this.ox + 30).cy(this.oy + yRevert(yScaling(tma)))
      .font({ size: 14, anchor: 'start' })
      .fill({ color: '#000' })
      .stroke({ color: '#222', width: '1' });//draw TMA text
    draw.line(this.ox, this.oy + yRevert(yScaling(tma)),
      this.ox + 25, this.oy + yRevert(yScaling(tma)))
      .stroke({ color: '#00f', width: 1.7, dasharray: '1,1' });//draw garis putus-putus untuk TMA
  }
} // class posTma

var Poses = [[238, "Kali Pepe - Tugu Boto", 96.65, 3.36, 3.86, 4.36, "-7.530121, 110.793746"], [239, "Kali Pepe - Tirtonadi", 89.60, 6.36, 6.86, 7.36, "-7.5509023, 110.8170868"], [240, "Jurug", 76.37, 3.36, 3.86, 4.36, "-7.566995, 110.861149"]];

/**
 * Mengubah array ke Obj
 * @param {Array} data fixed length dan urutan sesuai keys
 * @return {Object}
 */
let toObject = data => {
	const keys = ['id', 'nama', 'dasar', 'sh', 'sk', 'sm', 'll']
	let rv = {}
	for (let i=0; i < keys.length; ++i) {
		rv[keys[i]] = data[i]
	}
	return rv
}

const opt1 = toObject(Poses[0])
const opt2 = toObject(Poses[1])
const opt3 = toObject(Poses[2])

hMin = Math.min(dasar_1, dasar_2, dasar_3);
hMaks = Math.max((dasar_1 + sm_1), (dasar_2 + sm_2), (dasar_3 + sm_3)) + 0.5;

let Pos1 = new posTMA(opt1);
let Pos2 = new posTMA(opt2);
let Pos3 = new posTMA(opt3);

//const jarak_1_2 = distance(koordinat_1, koordinat_2);
const jarak_1_2 = Pos1.distanceTo(Pos2);
//const jarak_2_3 = distance(koordinat_2, koordinat_3);
const jarak_2_3 = Pos2.distanceTo(Pos3);

const xPositionPos2 = padding + ((jarak_1_2 / (jarak_1_2 + jarak_2_3)) * viewboxWidth);

Pos1.startDraw((viewboxWidth * 10 / 100) + padding, 0);//x = 10% dari kiri kanvas + padding
Pos1.updateTMA(98);
//createPos2.startDraw((viewboxWidth * 50 / 100), 0);//x = tengah kanvas
Pos2.startDraw(xPositionPos2, 0);//x = tengah kanvas
Pos2.updateTMA(92.6);

Pos3.startDraw((viewboxWidth * 90 / 100) - padding, 0);//x = 10% dari kanan kanvas + padding
Pos3.updateTMA(77);

draw.line((viewboxWidth * 10 / 100) + padding, 0 + yRevert(yScaling(hMin)),
  (viewboxWidth * 90 / 100) - padding, 0 + yRevert(yScaling(hMin)))
  .stroke({ color: '#222', width: 1.7, dasharray: '4,4' });//draw garis putus-putus antar POS
draw.text(jarak_1_2.toFixed(2).toString() + ' Km')
  .x((viewboxWidth * 20 / 100) + padding).cy(yRevert(yScaling(hMin)) - 10)
  .font({ size: 12, anchor: 'middle' })
  .fill({ color: '#000' })
  .stroke({ color: '#111', width: '0.5' });//draw Jarak Pos 1 ~ 2 text
draw.text(jarak_2_3.toFixed(2).toString() + ' Km')
  .x((viewboxWidth * 80 / 100) - padding).cy(yRevert(yScaling(hMin)) - 10)
  .font({ size: 12, anchor: 'middle' })
  .fill({ color: '#000' })
  .stroke({ color: '#111', width: '0.5' });//draw Jarak Pos 2 ~ 3 text
