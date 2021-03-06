#!/usr/bin/env python
#
# Copyright (c) 2013 Intel Corporation. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# pylint: disable=F0401

import distutils.dir_util
import optparse
import os
import shutil
import sys
import zipfile
from common_function import RemoveUnusedFilesInReleaseMode
from xml.dom.minidom import Document

LIBRARY_PROJECT_NAME = 'xwalk_core_library'
XWALK_CORE_SHELL_APK = 'xwalk_core_shell_apk'

def AddGeneratorOptions(option_parser):
  option_parser.add_option('-s', dest='source',
                           help='Source directory of project root.',
                           type='string')
  option_parser.add_option('-t', dest='target',
                           help='Product out target directory.',
                           type='string')


def CleanLibraryProject(out_dir):
  out_project_path = os.path.join(out_dir, LIBRARY_PROJECT_NAME)
  if os.path.exists(out_project_path):
    for item in os.listdir(out_project_path):
      sub_path = os.path.join(out_project_path, item)
      if os.path.isdir(sub_path):
        shutil.rmtree(sub_path)
      elif os.path.isfile(sub_path):
        os.remove(sub_path)


def CopyProjectFiles(project_source, out_dir):
  """cp xwalk/build/android/xwalkcore_library_template/<file>
        out/Release/xwalk_core_library/<file>
  """

  print 'Copying library project files...'
  template_dir = os.path.join(project_source, 'xwalk', 'build', 'android',
                              'xwalkcore_library_template')
  files_to_copy = [
      # AndroidManifest.xml from template.
      'AndroidManifest.xml',
      # Eclipse project properties from template.
      'project.properties',
      # Ant build file.
      'build.xml',
      # Ant properties file.
      'ant.properties',
  ]
  for f in files_to_copy:
    source_file = os.path.join(template_dir, f)
    target_file = os.path.join(out_dir, LIBRARY_PROJECT_NAME, f)

    shutil.copy2(source_file, target_file)


def CopyJSBindingFiles(project_source, out_dir):
  print 'Copying js binding files...'
  jsapi_dir = os.path.join(out_dir,
                           LIBRARY_PROJECT_NAME,
                           'res',
                           'raw')
  if not os.path.exists(jsapi_dir):
    os.makedirs(jsapi_dir)

  jsfiles_to_copy = [
      'xwalk/experimental/launch_screen/launch_screen_api.js',
      'xwalk/experimental/presentation/presentation_api.js',
      'xwalk/sysapps/device_capabilities/device_capabilities_api.js'
  ]

  # Copy JS binding file to assets/jsapi folder.
  for jsfile in jsfiles_to_copy:
    source_file = os.path.join(project_source, jsfile)
    target_file = os.path.join(jsapi_dir, os.path.basename(source_file))
    shutil.copyfile(source_file, target_file)


def CopyBinaries(out_dir):
  """cp out/Release/<pak> out/Release/xwalk_core_library/res/raw/<pak>
     cp out/Release/lib.java/<lib> out/Release/xwalk_core_library/libs/<lib>
     cp out/Release/xwalk_core_shell_apk/libs/*
        out/Release/xwalk_core_library/libs
  """

  print 'Copying binaries...'
  # Copy assets.
  res_raw_dir = os.path.join(
      out_dir, LIBRARY_PROJECT_NAME, 'res', 'raw')
  res_value_dir = os.path.join(
      out_dir, LIBRARY_PROJECT_NAME, 'res', 'values')
  if not os.path.exists(res_raw_dir):
    os.mkdir(res_raw_dir)
  if not os.path.exists(res_value_dir):
    os.mkdir(res_value_dir)

  paks_to_copy = [
      'icudtl.dat',
      'xwalk.pak',
  ]

  pak_list_xml = Document()
  resources_node = pak_list_xml.createElement('resources')
  string_array_node = pak_list_xml.createElement('string-array')
  string_array_node.setAttribute('name', 'xwalk_resources_list')
  pak_list_xml.appendChild(resources_node)
  resources_node.appendChild(string_array_node)
  for pak in paks_to_copy:
    source_file = os.path.join(out_dir, pak)
    target_file = os.path.join(res_raw_dir, pak)
    shutil.copyfile(source_file, target_file)
    item_node = pak_list_xml.createElement('item')
    item_node.appendChild(pak_list_xml.createTextNode(pak))
    string_array_node.appendChild(item_node)
  pak_list_file = open(os.path.join(res_value_dir,
                                    'xwalk_resources_list.xml'), 'w')
  pak_list_xml.writexml(pak_list_file, newl='\n', encoding='utf-8')
  pak_list_file.close()

  # Copy jar files to libs.
  libs_dir = os.path.join(out_dir, LIBRARY_PROJECT_NAME, 'libs')
  if not os.path.exists(libs_dir):
    os.mkdir(libs_dir)

  libs_to_copy = [
      'xwalk_core_library_java.jar',
  ]

  for lib in libs_to_copy:
    source_file = os.path.join(out_dir, 'lib.java', lib)
    target_file = os.path.join(libs_dir, lib)
    shutil.copyfile(source_file, target_file)

  # Copy native libraries.
  source_dir = os.path.join(out_dir, XWALK_CORE_SHELL_APK, 'libs')
  target_dir = libs_dir
  distutils.dir_util.copy_tree(source_dir, target_dir)


def CopyDirAndPrefixDuplicates(input_dir, output_dir, prefix):
  """ Copy the files into the output directory. If one file in input_dir folder
  doesn't exist, copy it directly. If a file exists, copy it and rename the
  file so that the resources won't be overrided. So all of them could be
  packaged into the xwalk core library.
  """
  for root, _, files in os.walk(input_dir):
    for f in files:
      src_file = os.path.join(root, f)
      relative_path = os.path.relpath(src_file, input_dir)
      target_file = os.path.join(output_dir, relative_path)
      target_dir_name = os.path.dirname(target_file)
      if not os.path.exists(target_dir_name):
        os.makedirs(target_dir_name)
      # If the file exists, copy it and rename it with another name to
      # avoid overwriting the existing one.
      if os.path.exists(target_file):
        target_base_name = os.path.basename(target_file)
        target_base_name = prefix + '_' + target_base_name
        target_file = os.path.join(target_dir_name, target_base_name)
      shutil.copyfile(src_file, target_file)


def MoveImagesToNonMdpiFolders(res_root):
  """Move images from drawable-*-mdpi-* folders to drawable-* folders.

  Why? http://crbug.com/289843

  Copied from build/android/gyp/package_resources.py.
  """
  for src_dir_name in os.listdir(res_root):
    src_components = src_dir_name.split('-')
    if src_components[0] != 'drawable' or 'mdpi' not in src_components:
      continue
    src_dir = os.path.join(res_root, src_dir_name)
    if not os.path.isdir(src_dir):
      continue
    dst_components = [c for c in src_components if c != 'mdpi']
    assert dst_components != src_components
    dst_dir_name = '-'.join(dst_components)
    dst_dir = os.path.join(res_root, dst_dir_name)
    if not os.path.isdir(dst_dir):
      os.makedirs(dst_dir)
    for src_file_name in os.listdir(src_dir):
      if not src_file_name.endswith('.png'):
        continue
      src_file = os.path.join(src_dir, src_file_name)
      dst_file = os.path.join(dst_dir, src_file_name)
      assert not os.path.lexists(dst_file)
      shutil.move(src_file, dst_file)


def CopyResources(out_dir):
  print 'Copying resources...'
  res_dir = os.path.join(out_dir, LIBRARY_PROJECT_NAME, 'res')
  temp_dir = os.path.join(out_dir, LIBRARY_PROJECT_NAME, 'temp')
  if os.path.exists(res_dir):
    shutil.rmtree(res_dir)
  if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)

  # All resources should be in specific folders in res_directory.
  # Since there might be some resource files with same names from
  # different folders like ui_java, content_java and others,
  # it's necessary to rename some files to avoid overridding.
  res_to_copy = [
      # zip file list
      'content_java.zip',
      'content_strings_grd.zip',
      'ui_java.zip',
      'ui_strings_grd.zip',
      'xwalk_core_internal_java.zip',
      'xwalk_core_strings.zip'
  ]

  for res_zip in res_to_copy:
    zip_file = os.path.join(out_dir, 'res.java', res_zip)
    zip_name = os.path.splitext(res_zip)[0]
    if not os.path.isfile(zip_file):
      raise Exception('Resource zip not found: ' + zip_file)
    subdir = os.path.join(temp_dir, zip_name)
    if os.path.isdir(subdir):
      raise Exception('Resource zip name conflict: ' + zip_name)
    os.makedirs(subdir)
    with zipfile.ZipFile(zip_file) as z:
      z.extractall(path=subdir)
    CopyDirAndPrefixDuplicates(subdir, res_dir, zip_name)
    MoveImagesToNonMdpiFolders(res_dir)

  if os.path.isdir(temp_dir):
    shutil.rmtree(temp_dir)


def PostCopyLibraryProject(out_dir):
  print 'Post Copy Library Project...'
  aidls_to_remove = [
      'org/chromium/content/common/common.aidl',
      'org/chromium/net/IRemoteAndroidKeyStoreInterface.aidl',
  ]
  for aidl in aidls_to_remove:
    aidl_file = os.path.join(out_dir, LIBRARY_PROJECT_NAME, 'src', aidl)
    if os.path.exists(aidl_file):
      os.remove(aidl_file)


def main(argv):
  print 'Generating XWalkCore Library Project...'
  option_parser = optparse.OptionParser()
  AddGeneratorOptions(option_parser)
  options, _ = option_parser.parse_args(argv)

  if not os.path.exists(options.source):
    print 'Source project does not exist, please provide correct directory.'
    sys.exit(1)
  out_dir = options.target

  # Clean directory for project first.
  CleanLibraryProject(out_dir)

  out_project_dir = os.path.join(out_dir, LIBRARY_PROJECT_NAME)
  if not os.path.exists(out_project_dir):
    os.mkdir(out_project_dir)

  # Copy Eclipse project files of library project.
  CopyProjectFiles(options.source, out_dir)
  # Copy binaries and resuorces.
  CopyResources(out_dir)
  CopyBinaries(out_dir)
  # Copy JS API binding files.
  CopyJSBindingFiles(options.source, out_dir)
  # Post copy library project.
  PostCopyLibraryProject(out_dir)
  # Remove unused files.
  mode = os.path.basename(os.path.normpath(out_dir))
  RemoveUnusedFilesInReleaseMode(mode,
      os.path.join(out_dir, LIBRARY_PROJECT_NAME, 'libs'))
  # Create empty src directory
  src_dir = os.path.join(out_project_dir, 'src')
  if not os.path.isdir(src_dir):
    os.mkdir(src_dir)
  readme = os.path.join(src_dir, 'README.md')
  open(readme, 'w').write(
      "# Source folder for xwalk_core_library\n"
      "## Why it's empty\n"
      "xwalk_core_library doesn't contain java sources.\n"
      "## Why put me here\n"
      "To make archives keep the folder, "
      "the src directory is needed to build an apk by ant.")
  print 'Your Android library project has been created at %s' % (
      out_project_dir)

if __name__ == '__main__':
  sys.exit(main(sys.argv))
