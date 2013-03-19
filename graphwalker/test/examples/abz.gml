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
			x	870.0
			y	450.0
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
			x	870.0
			y	510.0
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
			x	870.0
			y	570.0
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
			x	870.0
			y	630.0
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
	edge
	[
		source	0
		target	1
		label	"e_zero"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"e_zero"
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
		label	"e_one"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"e_one"
			fontSize	12
			fontName	"Dialog"
			model	"six_pos"
			position	"tail"
		]
	]
	edge
	[
		source	2
		target	3
		label	"e_two"
		graphics
		[
			fill	"#000000"
			targetArrow	"standard"
		]
		LabelGraphics
		[
			text	"e_two"
			fontSize	12
			fontName	"Dialog"
			model	"six_pos"
			position	"tail"
		]
	]
]
