Creator	"yFiles"
Version	"2.10"
graph
[
	hierarchic	1
	label	""
	directed	1
	node
	[
		id	0
		label	"Start"
		graphics
		[
			x	660.0
			y	360.0
			w	40.9765625
			h	30.0
			type	"rectangle"
			fill	"#FFCC00"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"Start"
			fontSize	12
			fontName	"Dialog"
			model	"null"
		]
	]
	node
	[
		id	1
		label	"v_a"
		graphics
		[
			x	660.0
			y	420.0
			w	32.837890625
			h	30.0
			type	"rectangle"
			fill	"#FFCC00"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"v_a"
			fontSize	12
			fontName	"Dialog"
			model	"null"
		]
	]
	node
	[
		id	2
		label	"v_b"
		graphics
		[
			x	632.59765625
			y	480.0
			w	33.763671875
			h	30.0
			type	"rectangle"
			fill	"#FFCC00"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"v_b"
			fontSize	12
			fontName	"Dialog"
			model	"null"
		]
	]
	node
	[
		id	3
		label	"v_c"
		graphics
		[
			x	692.59765625
			y	480.0
			w	32.357421875
			h	30.0
			type	"rectangle"
			fill	"#FFCC00"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"v_c"
			fontSize	12
			fontName	"Dialog"
			model	"null"
		]
	]
	node
	[
		id	4
		label	"v_d"
		graphics
		[
			x	662.59765625
			y	540.0
			w	33.763671875
			h	30.0
			type	"rectangle"
			fill	"#FFCC00"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"v_d"
			fontSize	12
			fontName	"Dialog"
			model	"null"
		]
	]
	node
	[
		id	5
		label	"v_e"
		graphics
		[
			x	782.59765625
			y	480.0
			w	32.896484375
			h	30.0
			type	"rectangle"
			fill	"#FFCC00"
			outline	"#000000"
		]
		LabelGraphics
		[
			text	"v_e"
			fontSize	12
			fontName	"Dialog"
			model	"null"
		]
	]
	edge
	[
		source	0
		target	1
		label	"e_once"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"e_once"
			fontSize	12
			fontName	"Dialog"
			model	"six_pos"
			position	"tail"
		]
	]
	edge
	[
		source	1
		target	2
		label	"e_eb"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"e_eb"
			fontSize	12
			fontName	"Dialog"
			model	"six_pos"
			position	"shead"
		]
	]
	edge
	[
		source	1
		target	3
		label	"e_ac"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"e_ac"
			fontSize	12
			fontName	"Dialog"
			model	"six_pos"
			position	"tail"
		]
	]
	edge
	[
		source	2
		target	4
		label	"e_bd"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"e_bd"
			fontSize	12
			fontName	"Dialog"
			model	"six_pos"
			position	"head"
		]
	]
	edge
	[
		source	3
		target	4
		label	"e_cd"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"e_cd"
			fontSize	12
			fontName	"Dialog"
			model	"six_pos"
			position	"stail"
		]
	]
	edge
	[
		source	4
		target	5
		label	"e_de"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"e_de"
			fontSize	12
			fontName	"Dialog"
			model	"six_pos"
			position	"stail"
		]
	]
	edge
	[
		source	5
		target	1
		label	"e_ea"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"e_ea"
			fontSize	12
			fontName	"Dialog"
			model	"six_pos"
			position	"shead"
		]
	]
]
