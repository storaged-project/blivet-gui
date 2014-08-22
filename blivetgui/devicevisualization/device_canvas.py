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

class device_canvas(Gtk.DrawingArea):
	
	def __init__(self, blivet_utils, ):
		Gtk.DrawingArea.__init__(self)

		self.b = blivet_utils
		self.connect('draw', self.draw_event)


	def visualize_device(self, partitions, partitions_list):

		self.partitions = partitions

		self.queue_draw()

	def draw_event(self, da, cairo_ctx):
		""" Drawing event for partition visualisation
		
			:param da: drawing area
			:type da: Gtk.DrawingArea
			:param cairo_ctx: Cairo context
			:type cairo_ctx: Cairo.Context
			
		"""
		
		# completely new visualisation tool is in progress, this one is really bad
		        
		width = da.get_allocated_width()
		height = da.get_allocated_height()
		
		total_size = 0
		num_parts = 0
		num_logical = 0
		
		cairo_ctx.set_source_rgb(1,1,1)
		cairo_ctx.paint()
		
		extended = False
		
		partitions = self.partitions
		
		for partition in partitions:
			
			if hasattr(partition, "isExtended") and partition.isExtended:
				extended = True # there is extended partition
			
			if hasattr(partition, "isLogical") and partition.isLogical:
				num_logical += 1
			
			else:
				total_size += partition.size.convertTo(spec="MiB")
				num_parts += 1
			
		#print "total size:", total_size, "num parts:", num_parts
		
		# Colors for partitions
		colors = [[0.451,0.824,0.086],
			[0.961,0.474,0],
			[0.204,0.396,0.643]]
		
		i = 0
		
		shrink = 0
		x = 0
		y = 0
		
		for partition in partitions:
			
			if hasattr(partition, "isLogical") and partition.isLogical:
				continue
			
			elif hasattr(partition, "isExtended") and partition.isExtended:
				extended_x = x
				extended_size = partition.size.convertTo(spec="MiB")
				cairo_ctx.set_source_rgb(0,1,1)
			
			elif hasattr(partition, "isFreeSpace") and partition.isFreeSpace:
				cairo_ctx.set_source_rgb(0.75, 0.75, 0.75)
				# Grey color for unallocated space
			
			else:
				cairo_ctx.set_source_rgb(colors[i % 3][0] , colors[i % 3][1], colors[i % 3][2])
				# Colors for other partitions/devices
			
			part_width = int(partition.size.convertTo(spec="MiB"))*(width - 2*shrink)/total_size
			
			#print part_width, partition[1]
			
			# Every partition need some minimum size in the drawing area
			# Minimum size = number of partitions*2 / width of draving area
			
			if part_width < width / (num_parts*2):
				part_width = width / (num_parts*2)
			
			elif part_width > width - ((num_parts-1)* (width / (num_parts*2))):
				part_width = width - (num_parts-1) * (width / (num_parts*2))
			
			if x + part_width > width:
				part_width = width - x
				
			if hasattr(partition, "isExtended") and partition.isExtended:
				extended_width = part_width
			
			#print "printing partition from", x, "to", x+part_width
			cairo_ctx.rectangle(x, shrink, part_width, height - 2*shrink)
			cairo_ctx.fill()
			
			cairo_ctx.set_source_rgb(0, 0, 0)
			cairo_ctx.select_font_face ("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL);
			cairo_ctx.set_font_size(10)
			
			# Print name of partition
			cairo_ctx.move_to(x + 12, height/2)
			cairo_ctx.show_text(partition.name)
			
			# Print size of partition
			cairo_ctx.move_to(x + 12 , height/2 + 12)
			cairo_ctx.show_text(str(partition.size))
			
			x += part_width
			i += 1
		
		if extended:
			
			# extended partition preset -> draw logical partitions
			
			extended_end = extended_x + extended_width
			
			# "border" space
			extended_x += 5
			extended_width -= 10
			
			#print "num_logical:", num_logical
			
			for partition in partitions:
				
				if hasattr(partition, "isFreeSpace") and partition.isFreeSpace:
					cairo_ctx.set_source_rgb(0.75, 0.75, 0.75)
					# Grey color for unallocated space
				
				else:
					cairo_ctx.set_source_rgb(colors[i % 3][0] , colors[i % 3][1], colors[i % 3][2])
					# Colors for other partitions/devices
				
				if hasattr(partition, "isLogical") and partition.isLogical:
					
					part_width = int(partition.size.convertTo(spec="MiB"))*(extended_width )/extended_size
					
					if part_width < (extended_width) / (num_logical*2):
						part_width = (extended_width) / (num_logical*2)
					
					elif part_width > (extended_width) - ((num_logical-1)* ((extended_width) / (num_logical*2))):
						part_width = (extended_width) - (num_logical-1) * ((extended_width) / (num_logical*2))
					
					if extended_x + part_width > extended_end:
						part_width = extended_end - extended_x - 5
						
					cairo_ctx.rectangle(extended_x, 5, part_width, height - 10)
					cairo_ctx.fill()
					
					cairo_ctx.set_source_rgb(0, 0, 0)
					cairo_ctx.select_font_face ("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL);
					cairo_ctx.set_font_size(10)
					
					# Print name of partition
					cairo_ctx.move_to(extended_x + 12, height/2)
					cairo_ctx.show_text(partition.name)
					
					# Print size of partition
					cairo_ctx.move_to(extended_x + 12 , height/2 + 12)
					cairo_ctx.show_text(str(partition.size))
					
					extended_x += part_width
					i += 1
		
		return True
		