import { create } from 'zustand'

type Sex='female'|'male'
type Goal='lose'|'maintain'|'gain'
type Activity='low'|'moderate'|'high'

type State={ 
  height:number; 
  weight:number; 
  age:number; 
  sex:Sex; 
  goal:Goal; 
  activity:Activity; 
  set:(p:Partial<State>)=>void 
}

export const useUser = create<State>((set)=>({
  height:170, 
  weight:65, 
  age:30, 
  sex:'female', 
  goal:'maintain', 
  activity:'moderate',
  set:(p)=>set(p),
}))