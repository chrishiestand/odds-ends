#!/usr/bin/env php
<?php

session_save_path('/tmp');
session_start();

function usage() {
  return basename(__FILE__) . " sessionfile1 [sessionfile2 ...]\n";
}

array_shift($argv);
if (empty($argv)) {
  echo usage();
  exit(0);
}

foreach ($argv as $file) {
  if (session_decode(file_get_contents($file))) {
    print_r($_SESSION);
    $_SESSION = array();
  }
  else {
    echo "Problem reading $file";
    exit(1);
  }
}
?>