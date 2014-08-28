# -*- coding: utf-8 -*-
# actions_history.py
# Store history of user selected actions
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

import copy as cp

class actions_history():
	""" Stores devicetree instances for undo-redo option
	"""
	
	def __init__(self, list_partitions):
		
		self.list_partitions = list_partitions
		
		self.undo_list = []
		self.redo_list = []
		
		self.undo_items = 0
		self.redo_items = 0
	
	def add_undo(self, devicetree, clear_redo=True):
		
		self.list_partitions.activate_options(["undo"])
		
		if self.undo_items == 5:
			self.undo_list.pop(0)
			self.undo_items -= 1
			
		self.undo_list.append(cp.deepcopy(devicetree))
		
		self.undo_items += 1

		if clear_redo:
			# clear redo list after adding new action
			self.redo_list = []
			self.redo_items = 0
			self.list_partitions.deactivate_options(["redo"])
		
		return
	
	def add_redo(self, devicetree):
		
		self.list_partitions.activate_options(["undo", "clear", "apply"])
		
		if self.redo_items == 5:
			self.redo_list.pop(0)
			self.redo_items -= 1
		
		self.redo_list.append(devicetree)
		self.redo_items += 1
				
		return
	
	def undo(self):
		
		self.add_redo(cp.deepcopy(self.list_partitions.b.storage.devicetree))
		
		self.list_partitions.activate_options(["undo", "redo"])
		
		self.undo_items -= 1
		
		if self.undo_items == 0:
			self.list_partitions.deactivate_options(["undo", "clear", "apply"])
					
		return self.undo_list.pop()
	
	def redo(self):
		
		self.add_undo(cp.deepcopy(self.list_partitions.b.storage.devicetree), False)
		
		self.redo_items -= 1
		
		self.list_partitions.activate_options(["clear", "apply"])
		
		if self.redo_items == 0:
			self.list_partitions.deactivate_options(["redo"])
		
		return self.redo_list.pop()
	
	def clear_history(self):
		""" Clear history after performing (or clearing) actions
		"""
		
		self.list_partitions.deactivate_options(["undo", "redo"])
			
		self.undo_items = 0
		self.redo_items = 0
		
		self.undo_list = []
		self.redo_list = []