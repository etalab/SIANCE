import React from "react";

import { Container, Dialog, Box } from "@material-ui/core";

import AnnotationRun, { AnsweredAnnotation } from "./AnnotationRun";
import AnnotationPrerun from "./AnnotationPrerun";
import useAnnotations from "../hooks/UseAnnotations";
import { sendAnnotations } from "../api/Api";

function AnnotationRunDialog({
  category,
  open,
  onValidate,
}: {
  category: string;
  open: boolean;
  onValidate: (annotations: AnsweredAnnotation[]) => void;
}) {
  const {data: annotations} = useAnnotations(category)
  return (
    <Dialog open={open} onClose={() => onValidate([])} fullWidth maxWidth="md">
      <AnnotationRun
        validate={onValidate}
        annotations={annotations || []}
      />
    </Dialog>
  );
}

function Annotate() {
  const [isRunning, setIsRunning] = React.useState<boolean>(false);
  const [category, setCategory] = React.useState<string>("Agressions")
  const [selectedCodes, setSelectedCodes] = React.useState<Set<string>>(
    new Set()
  );
  const saveAnnotations = function(annotations: AnsweredAnnotation[]) {
    // filter positive user response, and then remove this parameter to be formatted as "Annotation" 
    sendAnnotations(annotations.filter(a => a.userResponse).map(a=> {return {
      id_letter: a.id_letter,
      start: a.start,
      end: a.end,
      sentence: a.sentence,
      category: a.category,
      subcategory: a.subcategory,
      id_label: a.id_label,
      letter_name: a.letter_name,
      exploration: a.exploration
    }}))
  }

  return (
    <Container maxWidth="md">
      <AnnotationRunDialog category={category} open={isRunning} onValidate={(annotations) => {
        saveAnnotations(annotations)
        setIsRunning(false)
      }} />
        
      <Box p={2}>
        <AnnotationPrerun
          category={category}
          setCategory={setCategory}
          selectedCodes={selectedCodes}
          setSelectedCodes={setSelectedCodes}
          onValidate={() => setIsRunning(true)} 
        />
      </Box>
    </Container>
  );
}

export default Annotate;
