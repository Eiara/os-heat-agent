function test.function {
  source /etc/babashka/variables/test.sh
  
  system.file $TEST_PATH/test_file \
    -c $TEST_VALUE
}