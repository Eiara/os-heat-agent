function input.test.case() {
  source $VARIABLE_FILE
  
  system.file $OUTPUT_DIR/$FILE_NAME \
    -c "$TEST_VALUE"
}