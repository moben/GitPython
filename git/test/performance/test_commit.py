# test_performance.py
# Copyright (C) 2008, 2009 Michael Trier (mtrier@gmail.com) and contributors
#
# This module is part of GitPython and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

from lib import *
from git import *
from git import IStream
from git.test.test_commit import assert_commit_serialization
from cStringIO import StringIO
from time import time
import sys

class TestPerformance(TestBigRepoRW):

	# ref with about 100 commits in its history
	ref_100 = '0.1.6'

	def _query_commit_info(self, c):
		c.author
		c.authored_date
		c.author_tz_offset
		c.committer
		c.committed_date
		c.committer_tz_offset
		c.message
		c.parents
		
	def test_iteration(self):
		no = 0
		nc = 0
		
		# find the first commit containing the given path - always do a full 
		# iteration ( restricted to the path in question ), but in fact it should 
		# return quite a lot of commits, we just take one and hence abort the operation
		
		st = time()
		for c in self.rorepo.iter_commits(self.ref_100):
			nc += 1
			self._query_commit_info(c)
			for obj in c.tree.traverse():
				obj.size
				no += 1
			# END for each object
		# END for each commit
		elapsed_time = time() - st
		print >> sys.stderr, "Traversed %i Trees and a total of %i unchached objects in %s [s] ( %f objs/s )" % (nc, no, elapsed_time, no/elapsed_time) 
		
	def test_commit_traversal(self):
		# bound to cat-file parsing performance
		nc = 0
		st = time()
		for c in self.gitrorepo.commit(self.head_sha_2k).traverse(branch_first=False):
			nc += 1
			self._query_commit_info(c)
		# END for each traversed commit
		elapsed_time = time() - st
		print >> sys.stderr, "Traversed %i Commits in %s [s] ( %f commits/s )" % (nc, elapsed_time, nc/elapsed_time)
		
	def test_commit_iteration(self):
		# bound to stream parsing performance
		nc = 0
		st = time()
		for c in Commit.iter_items(self.gitrorepo, self.head_sha_2k):
			nc += 1
			self._query_commit_info(c)
		# END for each traversed commit
		elapsed_time = time() - st
		print >> sys.stderr, "Iterated %i Commits in %s [s] ( %f commits/s )" % (nc, elapsed_time, nc/elapsed_time)
		
	def test_commit_serialization(self):
		assert_commit_serialization(self.gitrwrepo, self.head_sha_2k, True)
		
		rwrepo = self.gitrwrepo
		make_object = rwrepo.odb.store
		# direct serialization - deserialization can be tested afterwards
		# serialization is probably limited on IO
		hc = rwrepo.commit(self.head_sha_2k)
		
		commits = list()
		nc = 5000
		st = time()
		for i in xrange(nc):
			cm = Commit(	rwrepo, Commit.NULL_BIN_SHA, hc.tree, 
							hc.author, hc.authored_date, hc.author_tz_offset, 
							hc.committer, hc.committed_date, hc.committer_tz_offset, 
							str(i), parents=hc.parents, encoding=hc.encoding)
			
			stream = StringIO()
			cm._serialize(stream)
			slen = stream.tell()
			stream.seek(0)
			
			cm.binsha = make_object(IStream(Commit.type, slen, stream)).binsha
		# END commit creation
		elapsed = time() - st
		
		print >> sys.stderr, "Serialized %i commits to loose objects in %f s ( %f commits / s )" % (nc, elapsed, nc / elapsed)
