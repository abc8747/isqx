import { createContext, useContext } from "solid-js";
import type { PublicApiPath } from "./types";

export const JumpContext = createContext<(path: PublicApiPath) => void>();
export const useJumper = () => useContext(JumpContext);
