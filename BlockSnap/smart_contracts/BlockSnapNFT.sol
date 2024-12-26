// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract BlockSnapNFT is ERC721URIStorage, Ownable {
    uint256 private _nextTokenId;
    
    // Mapping from token ID to IPFS CID
    mapping(uint256 => string) private _imageCIDs;
    
    // Events
    event PhotoMinted(uint256 indexed tokenId, address indexed owner, string ipfsCID, string metadataURI);
    
    constructor() ERC721("BlockSnap", "BSNAP") Ownable(msg.sender) {}
    
    /**
     * @dev Mint a new photo NFT
     * @param to The address that will own the minted token
     * @param imageCID The IPFS CID of the original photo
     * @param metadataURI The URI containing the metadata (usually IPFS URI)
     * @return uint256 The ID of the newly minted token
     */
    function mintPhoto(
        address to,
        string memory imageCID,
        string memory metadataURI
    ) public returns (uint256) {
        require(bytes(imageCID).length > 0, "Image CID cannot be empty");
        require(bytes(metadataURI).length > 0, "Metadata URI cannot be empty");
        
        uint256 tokenId = _nextTokenId++;
        
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, metadataURI);
        _imageCIDs[tokenId] = imageCID;
        
        emit PhotoMinted(tokenId, to, imageCID, metadataURI);
        
        return tokenId;
    }
    
    /**
     * @dev Get the IPFS CID for a specific token
     * @param tokenId The ID of the token
     * @return string The IPFS CID of the original photo
     */
    function getImageCID(uint256 tokenId) public view returns (string memory) {
        require(tokenId < _nextTokenId && bytes(_imageCIDs[tokenId]).length > 0, "Token does not exist");
        return _imageCIDs[tokenId];
    }
    
    /**
     * @dev Verify if a photo exists and get its owner
     * @param imageCID The IPFS CID to verify
     * @return bool Whether the photo exists
     * @return address The owner of the photo (zero address if not found)
     */
    function verifyPhoto(string memory imageCID) public view returns (bool, address) {
        for (uint256 i = 0; i < _nextTokenId; i++) {
            if (keccak256(bytes(_imageCIDs[i])) == keccak256(bytes(imageCID))) {
                return (true, ownerOf(i));
            }
        }
        return (false, address(0));
    }
    
    function burn(uint256 tokenId) public {
        require(ownerOf(tokenId) == msg.sender, "Not token owner");
        super._burn(tokenId);
    }
}