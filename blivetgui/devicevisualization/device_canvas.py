# -*- coding: utf-8 -*-
# dialogs.py
# Gtk.DrawingArea for device visualization
# 
# Copyright (C) 2014  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Vojtech Trefny <vtrefny@redhat.com>
#
#------------------------------------------------------------------------------# 

import os

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib

import gettext

import cairo

#------------------------------------------------------------------------------#

APP_NAME = "blivet-gui"

dirname, filename = os.path.split(os.path.abspath(__file__))

gettext.bindtextdomain('blivetgui', dirname + '/i18n')
gettext.textdomain('blivetgui')
_ = gettext.gettext

#------------------------------------------------------------------------------#

class cairo_rectangle():

	def __init__(self, x, y, width, height, color):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.color = color

class device_canvas(Gtk.DrawingArea):
	
	def __init__(self, blivet_utils):
		Gtk.DrawingArea.__init__(self)

		self.b = blivet_utils
		self.connect('draw', self.draw_event)
		self.rectangles = []

		self.color = 0

	def visualize_device(self, partitions, partitions_list, parent_device):

		self.partitions = partitions
		self.partitions_list = partitions_list
		self.parent = parent_device
		self.queue_draw()

	def detect_extended(self):
		""" Detect extended partitions

		"""

		extended = False
		num_logical = 0

		for partition in self.partitions:
			
			if hasattr(partition, "isExtended") and partition.isExtended:
				extended = True # there is extended partition
			
			if hasattr(partition, "isLogical") and partition.isLogical:
				num_logical += 1

		return (extended, num_logical)

	def pick_color(self, partition):

		if hasattr(partition, "isExtended") and partition.isExtended:
			return [0,1,1]

		elif hasattr(partition, "isFreeSpace") and partition.isFreeSpace:
			return [0.75, 0.75, 0.75]

		elif partition.format and partition.format.type == "lvmpv":
			return [0.8,0.6,0.4]
		elif partition.type == "lvmvg":
			return [0.38,0.35,0.5]
		elif partition.format and partition.format.type == "luks":
			return [0,0,0]
		else:
			self.color += 1
			return [[0.451,0.824,0.086],
			[0.961,0.474,0],
			[0.204,0.396,0.643]][self.color % 3]


	def compute_rectangles_size(self, partition, parent, parent_width, height, num_parts, start, depth):
		""" Compute sizes (in px) of partition rectangle

			:param partition: partition
			:type partition: TBD
			:param parent: parent device
			:type parent: TBD
			:param parent_width: size of parent 'element' (in px)
			:type parent_width: int
			:param height: canvas height
			:type height: int
			:param num_parts: number of partitions (children) for current parent
			:type num_parts: int
			:param start: starting x-coordinate
			:type start: int
			:param depth: current tree depth
			:type depth: int
			:returns: rectangle size and location
			:rtype: class:cairo_rectangle

		"""

		total_size = parent.size.convertTo(spec="MiB")
		
		if depth != 0:
			# 5px at the end for non-root devices (10 px = 5px for start + 5px for end)
			width = parent_width - 10
		
		else:
			width = parent_width
		
		x = start + depth
			
		part_width = int(partition.size.convertTo(spec="MiB"))*(width)/total_size
		
		# Every partition need some minimum size in the drawing area
		# Minimum size = number of partitions*2 / width of draving area
		
		if part_width < width / (num_parts*2):
			part_width = width / (num_parts*2)
		
		elif part_width > width - ((num_parts-1)* (width / (num_parts*2))):
			part_width = width - (num_parts-1) * (width / (num_parts*2))
		
		if part_width > width:
			part_width = width

		# [x, y, width, height, [r,g,b]]
		r = cairo_rectangle(x, depth, part_width, height - 2*depth, self.pick_color(partition))

		return r
			
		# #print "printing partition from", x, "to", x+part_width
		# cairo_ctx.rectangle(x, 0, part_width, height)
		# cairo_ctx.fill()
		
		# cairo_ctx.set_source_rgb(0, 0, 0)
		# cairo_ctx.select_font_face ("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL);
		# cairo_ctx.set_font_size(10)
		
		# # Print name of partition
		# cairo_ctx.move_to(x + 12, height/2)
		# cairo_ctx.show_text(partition.name)
		
		# # Print size of partition
		# cairo_ctx.move_to(x + 12 , height/2 + 12)
		# cairo_ctx.show_text(str(partition.size))

	def draw_rectangle(self, cairo_ctx, r):

		cairo_ctx.set_source_rgb(*r.color)
		cairo_ctx.rectangle(r.x, r.y, r.width, r.height)
		cairo_ctx.fill()


	def draw_event(self, da, cairo_ctx):
		""" Drawing event for partition visualisation
		
			:param da: drawing area
			:type da: Gtk.DrawingArea
			:param cairo_ctx: Cairo context
			:type cairo_ctx: Cairo.Context
			
		"""
		
		# paint the canvas     
		cairo_ctx.set_source_rgb(1,1,1)
		cairo_ctx.paint()

		# cavas size
		width = da.get_allocated_width()
		height = da.get_allocated_height()

		def draw_loop(self, treeiter, start, depth, parent, parent_size):

			# count number of partitions on current level
			num_parts = 0
			it = treeiter
			while it:
				num_parts += 1
				it = self.partitions_list.iter_next(it)

			while treeiter != None:
				rectangle = self.compute_rectangles_size(self.partitions_list[treeiter][0], parent, parent_size, height, num_parts, start, depth)
				self.draw_rectangle(cairo_ctx, rectangle)

				if self.partitions_list.iter_has_child(treeiter):
					childiter = self.partitions_list.iter_children(treeiter)
					draw_loop(self, childiter, start, depth + 5, self.partitions_list[treeiter][0], rectangle.width)

				start += rectangle.width
				treeiter = self.partitions_list.iter_next(treeiter)

			return

		root_iter = self.partitions_list.get_iter_first()
		draw_loop(self, root_iter, 0, 0, self.parent, width)

		return True
		