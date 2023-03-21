var provider = {
	states: [
		'Aceh', 'Sumatera Utara', 'Sumatera Barat', 'Jambi', 'Bangka Belitung',
		'Riau', 'Kepulauan Riau', 'Bengkulu', 'Sumatera Selatan', 'Lampung', 'Banten',
		'DKI Jakarta', 'Jawa Barat', 'Jawa Tengah', 'Jawa Timur', 'Nusa Tenggara Timur',
		'DI Yogyakarta', 'Bali', 'Nusa Tenggara Barat', 'Kalimantan Barat', 'Kalimantan Tengah',
		'Kalimantan Selatan', 'Kalimantan Timur', 'Kalimantan Utara', 'Sulawesi Selatan',
		'Sulawesi Utara', 'Gorontalo', 'Sulawesi Tengah', 'Sulawesi Barat', 'Sulawesi Tenggara',
		'Maluku', 'Maluku Utara', 'Papua Barat', 'Papua'
	],

	state_abbrs: [
		'Aceh', 'SumUt', 'SumBar', 'Jambi', 'BaBel',
		'Riau', 'KepR', 'Bengkulu', 'SumSel', 'Lampung', 'Banten',
		'DKI', 'JaBar', 'JaTeng', 'JaTim', 'NTT',
		'DIY', 'Bali', 'NTB', 'KalBar', 'KalTeng',
		'KalSel', 'KalTim', 'KalUt', 'SulSel',
		'SulUt', 'Gorontalo', 'SulTeng','SulBar', 'SulTra',
		'Maluku', 'MalUt', 'PapBar', 'Papua'
	],

	cities: [
		"Airmadidi", "Ampana", "Amurang", "Andolo", "Banggai", "Bantaeng", "Barru", "Bau-Bau", "Benteng", "Bitung", "Bolaang Uki", "Boroko", "Bulukumba", "Bungku", "Buol", "Buranga", "Donggala", "Enrekang", "Gorontalo", "Jeneponto", "Kawangkoan", "Kendari", "Kolaka", "Kotamobagu", "Kota Raha", "Kwandang", "Lasusua", "Luwuk", "Majene", "Makale", "Makassar", "Malili", "Mamasa", "Mamuju", "Manado", "Marisa", "Maros", "Masamba", "Melonguane", "Ondong Siau", "Palopo", "Palu", "Pangkajene", "Pare-Pare", "Parigi", "Pasangkayu", "Pinrang", "Polewali", "Poso", "Rantepao", "Ratahan", "Rumbia", "Sengkang", "Sidenreng", "Sigi Biromaru", "Sinjai", "Sunggu Minasa", "Suwawa", "Tahuna", "Takalar", "Tilamuta", "Toli Toli", "Tomohon", "Tondano", "Tutuyan", "Unaaha", "Wangi Wangi", "Wanggudu", "Watampone", "Watan Soppeng", "Ambarawa", "Anyer", "Bandung", "Bangil", "Banjar (Jawa Barat)", "Banjarnegara", "Bangkalan", "Bantul", "Banyumas", "Banyuwangi", "Batang", "Batu", "Bekasi", "Blitar", "Blora", "Bogor", "Bojonegoro", "Bondowoso", "Boyolali", "Bumiayu", "Brebes", "Caruban", "Cianjur", "Ciamis", "Cibinong", "Cikampek", "Cikarang", "Cilacap", "Cilegon", "Cirebon", "Demak", "Depok", "Garut", "Gresik", "Indramayu", "Jakarta", "Jember", "Jepara", "Jombang", "Kajen", "Karanganyar", "Kebumen", "Kediri", "Kendal", "Kepanjen", "Klaten", "Pelabuhan Ratu", "Kraksaan", "Kudus", "Kuningan", "Lamongan", "Lumajang", "Madiun", "Magelang", "Magetan", "Majalengka", "Malang", "Mojokerto", "Mojosari", "Mungkid", "Ngamprah", "Nganjuk", "Ngawi", "Pacitan", "Pamekasan", "Pandeglang", "Pare", "Pati", "Pasuruan", "Pekalongan", "Pemalang", "Ponorogo", "Probolinggo", "Purbalingga", "Purwakarta", "Purwodadi", "Purwokerto", "Purworejo", "Rangkasbitung", "Rembang", "Salatiga", "Sampang", "Semarang", "Serang", "Sidayu", "Sidoarjo", "Singaparna", "Situbondo", "Slawi", "Sleman", "Soreang", "Sragen", "Subang", "Sukabumi", "Sukoharjo", "Sumber", "Sumedang", "Sumenep", "Surabaya", "Surakarta", "Tasikmalaya", "Tangerang", "Tangerang Selatan", "Tegal", "Temanggung", "Tigaraksa", "Trenggalek", "Tuban", "Tulungagung", "Ungaran", "Wates", "Wlingi", "Wonogiri", "Wonosari", "Wonosobo", "Yogyakarta", "Atambua", "Baa", "Badung", "Bajawa", "Bangli", "Bima", "Denpasar", "Dompu", "Ende", "Gianyar", "Kalabahi", "Karangasem", "Kefamenanu", "Klungkung", "Kupang", "Labuhan Bajo", "Larantuka", "Lewoleba", "Maumere", "Mataram", "Mbay", "Negara", "Praya", "Raba", "Ruteng", "Selong", "Singaraja", "Soe", "Sumbawa Besar", "Tabanan", "Taliwang", "Tambolaka", "Tanjung", "Waibakul", "Waikabubak", "Waingapu", "Denpasar", "Negara,Bali", "Singaraja", "Tabanan", "Bangli"
	],

	city: function() {
		return this.random_element(this.cities);
	},

	state: function() {
		return this.random_element(this.states);
	},

	state_abbr: function() {
		return this.random_element(this.state_abbrs);
	}
};

module.exports = provider;
