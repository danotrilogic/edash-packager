#!/usr/bin/env python
#
# Copyright 2014 Google Inc. All rights reserved.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd
#
# This script is a wrapper for Packager that adds some support for how GYP
# is invoked by Packager.
#
# Build instructions:
#
# 1. Setup gyp: ./gyp_packager.py
#
# clang is not enabled by default, which can be enabled by overriding
# GYP_DEFINE environment variable, i.e.
# "GYP_DEFINES='clang=1' ./gyp_packager.py".
#
# Ninja is the default build system. User can also change to make by
# overriding GYP_GENERATORS to make, i.e.
# "GYP_GENERATORS='make' ./gyp_packager.py".
#
# 2. The first step generates the make files but does not start the
# build process. Ninja is the default build system. Refer to Ninja
# manual on how to do the build.
#
# Common syntaxes: ninja -C out/{Debug/Release} [Module]
# Module is optional. If not specified, build everything.
#
# Step 1 is only required if there is any gyp file change. Otherwise, you
# may just run ninja.

import os
import sys

checkout_dir = os.path.dirname(os.path.realpath(__file__))
src_dir = os.path.join(checkout_dir, 'packager')

sys.path.insert(0, os.path.join(src_dir, 'build'))
import gyp_helper  # Workaround the dynamic path. pylint: disable-msg=F0401

sys.path.insert(0, os.path.join(src_dir, 'tools', 'gyp', 'pylib'))
import gyp  # Workaround the dynamic path. pylint: disable-msg=F0401

if __name__ == '__main__':
  args = sys.argv[1:]

  # Allow src/.../chromium.gyp_env to define GYP variables.
  gyp_helper.apply_chromium_gyp_env()

  # If we didn't get a gyp file, then fall back to assuming 'packager.gyp' from
  # the same directory as the script.
  if [arg.endswith('.gyp') for arg in args].count(True) == 0:
    args.append(os.path.join(src_dir, 'packager.gyp'))

  # Always include common.gypi.
  args.extend(['-I' + os.path.join(src_dir, 'build', 'common.gypi')])

  # Set these default GYP_DEFINES if user does not set the value explicitly.
  _DEFAULT_DEFINES = {'test_isolation_mode': 'noop', 'use_glib': 0,
                      'use_openssl': 1, 'use_x11': 0,
                      'linux_use_gold_binary': 0, 'linux_use_gold_flags': 0}

  gyp_defines = (os.environ['GYP_DEFINES'] if os.environ.get('GYP_DEFINES')
                 else '')
  for key in _DEFAULT_DEFINES:
    if key not in gyp_defines:
      gyp_defines += ' {0}={1}'.format(key, _DEFAULT_DEFINES[key])
  os.environ['GYP_DEFINES'] = gyp_defines.strip()

  # There shouldn't be a circular dependency relationship between .gyp files,
  # but in Chromium's .gyp files, on non-Mac platforms, circular relationships
  # currently exist.  The check for circular dependencies is currently
  # bypassed on other platforms, but is left enabled on the Mac, where a
  # violation of the rule causes Xcode to misbehave badly.
  if sys.platform not in ('darwin',):
    args.append('--no-circular-check')

  # Default to ninja, but only if no generator has explicitly been set.
  if not os.environ.get('GYP_GENERATORS'):
    os.environ['GYP_GENERATORS'] = 'ninja'

  # TODO(kqyang): Find a better way to handle the depth. This workaround works
  # only if this script is executed in 'src' directory.
  if ['--depth' in arg for arg in args].count(True) == 0:
    args.append('--depth=packager')

  output_dir = os.path.join(checkout_dir, 'out')
  gyp_generator_flags = 'output_dir="' + output_dir + '"'
  if os.environ.get('GYP_GENERATOR_FLAGS'):
    os.environ['GYP_GENERATOR_FLAGS'] += ' ' + gyp_generator_flags
  else:
    os.environ['GYP_GENERATOR_FLAGS'] = gyp_generator_flags

  print 'Updating projects from gyp files...'
  sys.stdout.flush()

  # Off we go...
  sys.exit(gyp.main(args))
